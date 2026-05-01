import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
  CreateBucketCommand,
  DeleteObjectCommand,
  GetObjectCommand,
  HeadBucketCommand,
  HeadObjectCommand,
  ListObjectsV2Command,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { Readable } from 'node:stream';
import { randomUUID } from 'node:crypto';

export interface UploadInput {
  bucket?: string;
  key?: string;
  prefix?: string;
  filename: string;
  contentType: string;
  body: Buffer | Readable;
  metadata?: Record<string, string>;
}

@Injectable()
export class StorageService implements OnModuleInit {
  private readonly logger = new Logger('StorageService');
  readonly client: S3Client;
  /** Client dont l'endpoint est l'URL publique — pour les presigned URLs destinées au navigateur. */
  private readonly publicClient: S3Client;
  readonly defaultBucket: string;

  constructor(private readonly config: ConfigService) {
    const endpoint = config.get<string>('S3_ENDPOINT') ?? 'http://localhost:9000';
    const rawPublicUrl = config.get<string>('S3_PUBLIC_URL');
    const publicUrl = rawPublicUrl?.trim() ? rawPublicUrl.trim() : endpoint;
    if (!rawPublicUrl?.trim()) {
      this.logger.warn(
        `S3_PUBLIC_URL non défini : les URLs présignées utiliseront l'endpoint interne (${endpoint}) ` +
        `et seront inaccessibles depuis un navigateur. Définir S3_PUBLIC_URL=https://files.<domaine>.`,
      );
    } else if (publicUrl.includes('://minio')) {
      this.logger.warn(
        `S3_PUBLIC_URL pointe sur un nom de service interne (${publicUrl}). ` +
        `Les liens générés ne seront pas atteignables depuis un navigateur. ` +
        `Utiliser le FQDN public exposé par Caddy / Traefik.`,
      );
    }
    const region = config.get<string>('S3_REGION') ?? 'us-east-1';
    const accessKeyId = config.get<string>('S3_ACCESS_KEY') ?? 'minio';
    const secretAccessKey = config.get<string>('S3_SECRET_KEY') ?? 'minio12345';
    const forcePathStyle = (config.get<string>('S3_FORCE_PATH_STYLE') ?? 'true') === 'true';

    const credentials = { accessKeyId, secretAccessKey };
    this.defaultBucket = config.get<string>('S3_BUCKET') ?? 'senlegal';

    this.client = new S3Client({
      endpoint,
      region,
      credentials,
      forcePathStyle,
    });

    this.publicClient = new S3Client({
      endpoint: publicUrl,
      region,
      credentials,
      forcePathStyle,
    });
  }

  async onModuleInit() {
    await this.ensureBucket(this.defaultBucket);
  }

  async ensureBucket(bucket: string) {
    try {
      await this.client.send(new HeadBucketCommand({ Bucket: bucket }));
    } catch {
      try {
        await this.client.send(new CreateBucketCommand({ Bucket: bucket }));
        this.logger.log(`bucket created: ${bucket}`);
      } catch (e) {
        this.logger.warn(`could not create bucket ${bucket}: ${(e as Error).message}`);
      }
    }
  }

  buildKey(prefix: string, filename: string): string {
    const safe = filename.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 200);
    const stamp = new Date().toISOString().slice(0, 10);
    return `${prefix.replace(/\/$/, '')}/${stamp}/${randomUUID()}-${safe}`;
  }

  async upload(input: UploadInput) {
    const bucket = input.bucket ?? this.defaultBucket;
    const key =
      input.key ?? this.buildKey(input.prefix ?? 'misc', input.filename);
    await this.client.send(
      new PutObjectCommand({
        Bucket: bucket,
        Key: key,
        Body: input.body,
        ContentType: input.contentType,
        Metadata: input.metadata,
      }),
    );
    return { bucket, key };
  }

  async getSignedDownloadUrl(bucket: string, key: string, expiresIn = 300): Promise<string> {
    return getSignedUrl(
      this.publicClient,
      new GetObjectCommand({ Bucket: bucket, Key: key }),
      { expiresIn },
    );
  }

  async getStream(bucket: string, key: string): Promise<Readable> {
    const out = await this.client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    return out.Body as Readable;
  }

  async getBuffer(bucket: string, key: string): Promise<Buffer> {
    const out = await this.client.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
    const body = out.Body as Readable;
    const chunks: Buffer[] = [];
    for await (const chunk of body) {
      chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : Buffer.from(chunk as Uint8Array));
    }
    return Buffer.concat(chunks);
  }

  async exists(bucket: string, key: string): Promise<boolean> {
    try {
      await this.client.send(new HeadObjectCommand({ Bucket: bucket, Key: key }));
      return true;
    } catch {
      return false;
    }
  }

  async delete(bucket: string, key: string): Promise<void> {
    await this.client.send(new DeleteObjectCommand({ Bucket: bucket, Key: key }));
  }

  async *streamAllObjects(bucket: string, prefix?: string) {
    let token: string | undefined;
    do {
      const out = await this.client.send(
        new ListObjectsV2Command({
          Bucket: bucket,
          Prefix: prefix,
          ContinuationToken: token,
        }),
      );
      for (const o of out.Contents ?? []) {
        if (!o.Key) continue;
        yield o;
      }
      token = out.IsTruncated ? out.NextContinuationToken : undefined;
    } while (token);
  }
}
