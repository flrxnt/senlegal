import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { AnalyticsEventType, DocumentKind, Plan, UserRole } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';
import { AiService } from '../ai/ai.service';
import { PlanLimitsService } from '../../common/plans/plan-limits.service';
import { AnalyticsService } from '../analytics/analytics.service';

@Injectable()
export class DocumentsService {
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
    const { bucket, key } = await this.storage.upload({
      prefix: 'rag/sources',
      filename: file.originalname,
      contentType: file.mimetype,
      body: file.buffer,
    });
    let ingestResult: unknown = null;
    try {
      ingestResult = await this.ai.ingest(file.buffer, file.originalname, file.mimetype);
    } catch (e) {
      // Persist record anyway so admin can retry.
      ingestResult = { error: (e as Error).message };
    }
    const doc = await this.prisma.document.create({
      data: {
        ownerId: adminId,
        kind: DocumentKind.RAG_SOURCE,
        bucket,
        objectKey: key,
        filename: file.originalname,
        contentType: file.mimetype,
        sizeBytes: file.size,
        ingestedAt: new Date(),
        metadata: ingestResult ? (ingestResult as object) : undefined,
      },
    });
    return doc;
  }

  async deleteRagSource(id: string) {
    const doc = await this.prisma.document.findUnique({ where: { id } });
    if (!doc || doc.kind !== DocumentKind.RAG_SOURCE) throw new NotFoundException();
    await this.storage.delete(doc.bucket, doc.objectKey).catch(() => { });
    await this.prisma.document.delete({ where: { id } });
    return { ok: true };
  }
}
