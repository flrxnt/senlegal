import { BadRequestException, Injectable, Logger, NotFoundException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Client } from 'pg';
import archiver from 'archiver';
import unzipper from 'unzipper';
import { PassThrough, Readable } from 'node:stream';
import { Upload } from '@aws-sdk/lib-storage';
import { GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';

// Order in which to dump/restore tables (parents first to ease restore).
const TABLE_ORDER = [
  'User',
  'PasswordResetToken',
  'Conversation',
  'Message',
  'Document',
  'Subscription',
  'Invoice',
  'AnalyticsEvent',
  'ErrorLog',
];

const BACKUP_PREFIX = 'backups/';

@Injectable()
export class BackupService {
  private readonly logger = new Logger('BackupService');

  constructor(
    private readonly prisma: PrismaService,
    private readonly storage: StorageService,
    private readonly config: ConfigService,
  ) { }

  // --- Database ----------------------------------------------------------

  async dumpAllTables(): Promise<Record<string, unknown[]>> {
    const url = this.config.get<string>('DATABASE_URL');
    if (!url) throw new Error('DATABASE_URL missing.');
    const client = new Client({ connectionString: url });
    await client.connect();
    const out: Record<string, unknown[]> = {};
    try {
      for (const t of TABLE_ORDER) {
        const r = await client.query(`SELECT * FROM "${t}"`);
        out[t] = r.rows;
      }
    } finally {
      await client.end();
    }
    return out;
  }

  async restoreAllTables(data: Record<string, unknown[]>): Promise<{ restored: Record<string, number> }> {
    const url = this.config.get<string>('DATABASE_URL');
    if (!url) throw new Error('DATABASE_URL missing.');
    const client = new Client({ connectionString: url });
    await client.connect();
    const restored: Record<string, number> = {};
    try {
      await client.query("SET session_replication_role = 'replica'");
      for (const table of TABLE_ORDER) {
        const rows = data[table];
        if (!Array.isArray(rows) || rows.length === 0) {
          restored[table] = 0;
          continue;
        }
        const cols = Object.keys(rows[0] as object);
        const colList = cols.map((c) => `"${c}"`).join(', ');
        let inserted = 0;
        for (const row of rows) {
          const values = cols.map((c) => (row as Record<string, unknown>)[c]);
          const placeholders = values.map((_, i) => `$${i + 1}`).join(', ');
          try {
            await client.query(
              `INSERT INTO "${table}" (${colList}) VALUES (${placeholders}) ON CONFLICT DO NOTHING`,
              values,
            );
            inserted += 1;
          } catch (e) {
            this.logger.warn(`restore ${table}: ${(e as Error).message}`);
          }
        }
        restored[table] = inserted;
      }
    } finally {
      await client.query("SET session_replication_role = 'origin'").catch(() => { });
      await client.end();
    }
    return { restored };
  }

  // --- Combined backups (DB + storage) -----------------------------------

  /** Stream a zip backup directly to MinIO/S3 and persist a Document row. */
  async createFullBackup(adminId: string | null): Promise<{ key: string; bucket: string }> {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const key = `${BACKUP_PREFIX}${ts}-full.zip`;
    const bucket = this.storage.defaultBucket;

    const archive = archiver('zip', { zlib: { level: 6 } });
    const passthrough = new PassThrough();
    archive.pipe(passthrough);

    const upload = new Upload({
      client: this.storage.client,
      params: {
        Bucket: bucket,
        Key: key,
        Body: passthrough,
        ContentType: 'application/zip',
      },
    });

    // Database dump
    const data = await this.dumpAllTables();
    archive.append(JSON.stringify(data, null, 2), { name: 'database.json' });

    // Storage objects (everything except other backups)
    for await (const obj of this.storage.streamAllObjects(bucket)) {
      if (!obj.Key || obj.Key.startsWith(BACKUP_PREFIX)) continue;
      try {
        const out = await this.storage.client.send(
          new GetObjectCommand({ Bucket: bucket, Key: obj.Key }),
        );
        archive.append(out.Body as Readable, { name: `storage/${obj.Key}` });
      } catch (e) {
        this.logger.warn(`backup: cannot fetch ${obj.Key}: ${(e as Error).message}`);
      }
    }

    archive.finalize().catch(() => undefined);
    await upload.done();

    return { key, bucket };
  }

  async createDatabaseBackup(): Promise<{ key: string; bucket: string }> {
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    const key = `${BACKUP_PREFIX}${ts}-database.json`;
    const bucket = this.storage.defaultBucket;
    const data = await this.dumpAllTables();
    await this.storage.client.send(
      new PutObjectCommand({
        Bucket: bucket,
        Key: key,
        Body: JSON.stringify(data, null, 2),
        ContentType: 'application/json',
      }),
    );
    return { key, bucket };
  }

  async listBackups() {
    const out: Array<{ key: string; size: number; lastModified: Date | null }> = [];
    for await (const obj of this.storage.streamAllObjects(this.storage.defaultBucket, BACKUP_PREFIX)) {
      out.push({
        key: obj.Key!,
        size: obj.Size ?? 0,
        lastModified: obj.LastModified ?? null,
      });
    }
    return out.sort((a, b) => (a.key < b.key ? 1 : -1));
  }

  async getDownloadUrl(key: string) {
    if (!key.startsWith(BACKUP_PREFIX)) throw new BadRequestException('Clé invalide.');
    const exists = await this.storage.exists(this.storage.defaultBucket, key);
    if (!exists) throw new NotFoundException();
    const url = await this.storage.getSignedDownloadUrl(this.storage.defaultBucket, key, 600);
    return { url, expiresIn: 600 };
  }

  async deleteBackup(key: string) {
    if (!key.startsWith(BACKUP_PREFIX)) throw new BadRequestException('Clé invalide.');
    await this.storage.delete(this.storage.defaultBucket, key);
    return { ok: true };
  }

  /**
   * Restore from an uploaded archive (`.json` = database only ; `.zip` = full).
   * Returns counts. NOT idempotent — uses ON CONFLICT DO NOTHING.
   */
  async restoreFromUpload(file: Express.Multer.File) {
    if (!file) throw new BadRequestException('Aucun fichier.');
    const name = file.originalname.toLowerCase();
    if (name.endsWith('.json')) {
      const data = JSON.parse(file.buffer.toString('utf-8')) as Record<string, unknown[]>;
      return this.restoreAllTables(data);
    }
    if (name.endsWith('.zip')) {
      const dir = await unzipper.Open.buffer(file.buffer);
      const dbEntry = dir.files.find((f) => f.path === 'database.json');
      if (!dbEntry) throw new BadRequestException('database.json absent du zip.');
      const buf = await dbEntry.buffer();
      const data = JSON.parse(buf.toString('utf-8')) as Record<string, unknown[]>;
      const dbResult = await this.restoreAllTables(data);

      let storageRestored = 0;
      for (const f of dir.files) {
        if (!f.path.startsWith('storage/') || f.type !== 'File') continue;
        const objectKey = f.path.slice('storage/'.length);
        const data = await f.buffer();
        await this.storage.client.send(
          new PutObjectCommand({
            Bucket: this.storage.defaultBucket,
            Key: objectKey,
            Body: data,
          }),
        );
        storageRestored += 1;
      }
      return { ...dbResult, storageRestored };
    }
    throw new BadRequestException('Extension non supportée (.json ou .zip).');
  }
}
