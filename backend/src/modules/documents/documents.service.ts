import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  Logger,
  NotFoundException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AnalyticsEventType, DocumentKind, IngestStatus, Plan, UserRole } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';
import { AiService } from '../ai/ai.service';
import { PlanLimitsService } from '../../common/plans/plan-limits.service';
import { AnalyticsService } from '../analytics/analytics.service';

@Injectable()
export class DocumentsService {
  private readonly logger = new Logger('DocumentsService');
  constructor(
    private readonly prisma: PrismaService,
    private readonly storage: StorageService,
    private readonly ai: AiService,
    private readonly limits: PlanLimitsService,
    private readonly analytics: AnalyticsService,
    private readonly config: ConfigService,
  ) { }

  async listMine(userId: string) {
    const items = await this.prisma.document.findMany({
      where: { ownerId: userId, kind: { in: [DocumentKind.USER_PRIVATE, DocumentKind.CHAT_ATTACHMENT] } },
      orderBy: { createdAt: 'desc' },
    });
    return items;
  }

  async uploadMine(
    userId: string,
    plan: Plan,
    file: Express.Multer.File,
    kind: DocumentKind = DocumentKind.USER_PRIVATE,
  ) {
    if (!file) throw new BadRequestException('Aucun fichier fourni.');
    if (kind !== DocumentKind.USER_PRIVATE && kind !== DocumentKind.CHAT_ATTACHMENT) {
      throw new BadRequestException('kind invalide.');
    }
    const limits = this.limits.getLimits(plan);
    const maxMb = kind === DocumentKind.CHAT_ATTACHMENT ? limits.maxChatAttachmentMb : limits.maxUserDocumentMb;
    if (file.size > maxMb * 1024 * 1024) {
      throw new BadRequestException(`Fichier trop volumineux (max ${maxMb} MB).`);
    }
    await this.limits.assertCanUpload(userId, plan, file.size);

    const prefix = kind === DocumentKind.CHAT_ATTACHMENT
      ? `users/${userId}/chat`
      : `users/${userId}/private`;
    const { bucket, key } = await this.storage.upload({
      prefix,
      filename: file.originalname,
      contentType: file.mimetype,
      body: file.buffer,
    });
    const doc = await this.prisma.document.create({
      data: {
        ownerId: userId,
        kind,
        bucket,
        objectKey: key,
        filename: file.originalname,
        contentType: file.mimetype,
        sizeBytes: file.size,
      },
    });
    await this.analytics.track(AnalyticsEventType.DOCUMENT_UPLOADED, userId, {}, {
      kind,
      sizeBytes: file.size,
    });
    return doc;
  }

  async getDownloadUrl(docId: string, userId: string, role: UserRole) {
    const doc = await this.prisma.document.findUnique({ where: { id: docId } });
    if (!doc) throw new NotFoundException();
    if (role !== UserRole.ADMIN && doc.ownerId && doc.ownerId !== userId) {
      throw new ForbiddenException();
    }
    const url = await this.storage.getSignedDownloadUrl(doc.bucket, doc.objectKey);
    return { url, expiresIn: 300, document: doc };
  }

  async deleteMine(docId: string, userId: string) {
    const doc = await this.prisma.document.findUnique({ where: { id: docId } });
    if (!doc) throw new NotFoundException();
    if (doc.ownerId !== userId) throw new ForbiddenException();
    if (doc.kind === DocumentKind.RAG_SOURCE) throw new ForbiddenException('Document RAG protégé.');
    await this.storage.delete(doc.bucket, doc.objectKey).catch(() => { });
    await this.prisma.document.delete({ where: { id: docId } });
    return { ok: true };
  }

  // ----- ADMIN: RAG ingestion ---------------------------------------------

  async listRagSources() {
    return this.prisma.document.findMany({
      where: { kind: DocumentKind.RAG_SOURCE },
      orderBy: { createdAt: 'desc' },
    });
  }

  async ingestRagSource(adminId: string, file: Express.Multer.File) {
    if (!file) throw new BadRequestException('Aucun fichier fourni.');
    const maxMb = Number(this.config.get('MAX_RAG_DOCUMENT_SIZE_MB') ?? 100);
    if (file.size > maxMb * 1024 * 1024) {
      throw new BadRequestException(`Fichier trop volumineux (max ${maxMb} MB).`);
    }
    if (file.mimetype && !file.mimetype.toLowerCase().includes('pdf')) {
      throw new BadRequestException('Seuls les fichiers PDF sont acceptés.');
    }
    // 1. Upload vers MinIO (source de vérité — la ré-indexation re-télécharge depuis ici)
    const { bucket, key } = await this.storage.upload({
      prefix: 'rag/sources',
      filename: file.originalname,
      contentType: file.mimetype,
      body: file.buffer,
    });
    // 2. Persiste le Document en statut PENDING (admin voit immédiatement la source)
    const doc = await this.prisma.document.create({
      data: {
        ownerId: adminId,
        kind: DocumentKind.RAG_SOURCE,
        bucket,
        objectKey: key,
        filename: file.originalname,
        contentType: file.mimetype,
        sizeBytes: file.size,
        ingestStatus: IngestStatus.PENDING,
      },
    });
    // 3. Lance l'indexation AI en arrière-plan, sans bloquer la réponse HTTP.
    //    Le frontend peut poller /admin/rag/sources pour suivre le statut.
    this.runIngestionInBackground(doc.id, file.buffer, file.originalname, file.mimetype);
    return doc;
  }

  /** Re-déclenche l'indexation pour une source existante (re-télécharge depuis MinIO). */
  async reingestRagSource(id: string) {
    const doc = await this.prisma.document.findUnique({ where: { id } });
    if (doc?.kind !== DocumentKind.RAG_SOURCE) throw new NotFoundException();
    if (doc.ingestStatus === IngestStatus.PROCESSING) {
      throw new BadRequestException('Une indexation est déjà en cours pour ce document.');
    }
    const updated = await this.prisma.document.update({
      where: { id },
      data: {
        ingestStatus: IngestStatus.PENDING,
        ingestError: null,
      },
    });
    // Pull bytes depuis MinIO puis lance l'ingestion en arrière-plan.
    this.storage
      .getBuffer(doc.bucket, doc.objectKey)
      .then((buffer) =>
        this.runIngestionInBackground(doc.id, buffer, doc.filename, doc.contentType),
      )
      .catch(async (e) => {
        this.logger.error(`reingest ${id} download failed: ${(e as Error).message}`);
        await this.prisma.document
          .update({
            where: { id },
            data: {
              ingestStatus: IngestStatus.FAILED,
              ingestError: `Téléchargement MinIO impossible : ${(e as Error).message}`,
            },
          })
          .catch(() => undefined);
      });
    return updated;
  }

  /** Déclenche l'ingestion AI en arrière-plan et met à jour le statut du Document. */
  private runIngestionInBackground(
    docId: string,
    buffer: Buffer,
    filename: string,
    contentType: string,
  ): void {
    void (async () => {
      const startedAt = new Date();
      try {
        await this.prisma.document.update({
          where: { id: docId },
          data: {
            ingestStatus: IngestStatus.PROCESSING,
            ingestStartedAt: startedAt,
            ingestError: null,
          },
        });
        const result = await this.ai.ingest(buffer, filename, contentType, docId);
        await this.prisma.document.update({
          where: { id: docId },
          data: {
            ingestStatus: IngestStatus.READY,
            ingestedAt: new Date(),
            ingestError: null,
            metadata: result ? (result as object) : undefined,
          },
        });
        this.logger.log(`ingestion ok doc=${docId} (${filename})`);
      } catch (e) {
        const msg = (e as Error).message ?? String(e);
        this.logger.error(`ingestion failed doc=${docId}: ${msg}`);
        await this.prisma.document
          .update({
            where: { id: docId },
            data: {
              ingestStatus: IngestStatus.FAILED,
              ingestError: msg.slice(0, 1000),
            },
          })
          .catch(() => undefined);
      }
    })();
  }

  async deleteRagSource(id: string) {
    const doc = await this.prisma.document.findUnique({ where: { id } });
    if (doc?.kind !== DocumentKind.RAG_SOURCE) throw new NotFoundException();
    // 1. Désindexe côté AI (best-effort — on n'empêche pas la suppression si l'AI est down)
    await this.ai.deleteIngestSource(id).catch((e) => {
      this.logger.warn(`AI deleteIngestSource ${id} failed: ${(e as Error).message}`);
    });
    // 2. Supprime le binaire dans MinIO
    await this.storage.delete(doc.bucket, doc.objectKey).catch((e) => {
      this.logger.warn(`MinIO delete ${doc.objectKey} failed: ${(e as Error).message}`);
    });
    // 3. Supprime la ligne Postgres
    await this.prisma.document.delete({ where: { id } });
    return { ok: true };
  }
}
