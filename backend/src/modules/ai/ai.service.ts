import { BadGatewayException, Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Readable } from 'node:stream';

export interface AiHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AiChatRequest {
  question: string;
  topK?: number;
  history?: AiHistoryMessage[];
}

export interface AiCitation {
  article_number: string;
  article_title?: string | null;
  document: string;
  volume?: string | null;
  section?: string | null;
  page: number;
  snippet: string;
  score?: number | null;
}

export interface AiChatResponse {
  answer: string;
  citations: AiCitation[];
  used_context: boolean;
  rewritten_question?: string | null;
}

const RETRY_STATUS = new Set([502, 503, 504]);

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

@Injectable()
export class AiService {
  private readonly logger = new Logger('AiService');
  private readonly baseUrl: string;
  private readonly apiKey?: string;
  private readonly adminToken?: string;
  private readonly timeoutMs: number;

  constructor(config: ConfigService) {
    this.baseUrl = (config.get<string>('AI_BASE_URL') ?? 'http://localhost:8001').replace(/\/$/, '');
    this.apiKey = config.get<string>('AI_API_KEY') || undefined;
    this.adminToken = config.get<string>('AI_ADMIN_TOKEN') || undefined;
    this.timeoutMs = Number(config.get('AI_TIMEOUT_MS') ?? 60_000);
  }

  private headers(extra?: Record<string, string>): Record<string, string> {
    const h: Record<string, string> = { 'Content-Type': 'application/json', ...extra };
    if (this.apiKey) h['X-API-Key'] = this.apiKey;
    return h;
  }

  private buildBody(req: AiChatRequest) {
    return JSON.stringify({
      question: req.question,
      top_k: req.topK,
      history: req.history ?? [],
    });
  }

  private async fetchWithRetry(path: string, init: RequestInit, retries = 2): Promise<Response> {
    let attempt = 0;
    let lastErr: unknown;
    while (attempt <= retries) {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), this.timeoutMs);
      try {
        const res = await fetch(`${this.baseUrl}${path}`, { ...init, signal: ctrl.signal });
        clearTimeout(t);
        if (!RETRY_STATUS.has(res.status)) return res;
        lastErr = new Error(`AI ${path} -> HTTP ${res.status}`);
      } catch (e) {
        clearTimeout(t);
        lastErr = e;
      }
      attempt += 1;
      if (attempt <= retries) await sleep(300 * attempt);
    }
    throw new BadGatewayException(`AI service unavailable: ${(lastErr as Error)?.message}`);
  }

  async chat(req: AiChatRequest): Promise<AiChatResponse> {
    const res = await this.fetchWithRetry('/chat', {
      method: 'POST',
      headers: this.headers(),
      body: this.buildBody(req),
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new BadGatewayException(`AI /chat error ${res.status}: ${txt}`);
    }
    return (await res.json()) as AiChatResponse;
  }

  async chatStream(req: AiChatRequest): Promise<Response> {
    const res = await this.fetchWithRetry('/chat/stream', {
      method: 'POST',
      headers: this.headers({ Accept: 'text/event-stream' }),
      body: this.buildBody(req),
    });
    if (!res.ok || !res.body) {
      const txt = await res.text().catch(() => '');
      throw new BadGatewayException(`AI /chat/stream error ${res.status}: ${txt}`);
    }
    return res;
  }

  async search(query: string, topK = 5): Promise<{ results: AiCitation[] }> {
    const res = await this.fetchWithRetry('/search', {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify({ query, top_k: topK }),
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new BadGatewayException(`AI /search error ${res.status}: ${txt}`);
    }
    return (await res.json()) as { results: AiCitation[] };
  }

  async ingest(
    buffer: Buffer,
    filename: string,
    contentType: string,
    sourceId: string,
  ): Promise<unknown> {
    const adminHeaders: Record<string, string> = {};
    if (this.apiKey) adminHeaders['X-API-Key'] = this.apiKey;
    if (this.adminToken) adminHeaders['X-Admin-Token'] = this.adminToken;

    // 1. Soumet le fichier — retourne 202 immédiatement.
    const form = new FormData();
    const blob = new Blob([new Uint8Array(buffer)], { type: contentType });
    form.append('file', blob, filename);
    form.append('source_id', sourceId);

    const submitRes = await fetch(`${this.baseUrl}/ingest/file`, {
      method: 'POST',
      headers: adminHeaders,
      body: form as unknown as BodyInit,
    });
    if (!submitRes.ok) {
      const txt = await submitRes.text().catch(() => '');
      throw new BadGatewayException(`AI /ingest/file error ${submitRes.status}: ${txt}`);
    }

    // 2. Poll le statut jusqu'à complétion ou échec.
    const pollIntervalMs = 5_000;
    const maxWaitMs = 60 * 60_000; // 1 h max
    const start = Date.now();

    while (Date.now() - start < maxWaitMs) {
      await sleep(pollIntervalMs);
      try {
        const statusRes = await fetch(
          `${this.baseUrl}/ingest/status/${encodeURIComponent(sourceId)}`,
          { headers: { ...adminHeaders, 'Content-Type': 'application/json' } },
        );
        if (!statusRes.ok) continue;
        const data = (await statusRes.json()) as Record<string, unknown>;
        const s = data.status as string;

        if (s === 'ok' || s === 'empty') return data;
        if (s === 'failed') {
          throw new BadGatewayException(`AI ingestion failed: ${data.error ?? 'unknown'}`);
        }
        if (s === 'processing') {
          const done = data.chunks_done ?? 0;
          const total = data.chunks_total ?? '?';
          this.logger.log(`ingest ${sourceId}: ${done}/${total} chunks`);
        }
      } catch (e) {
        if (e instanceof BadGatewayException) throw e;
        this.logger.warn(`ingest poll error: ${(e as Error).message}`);
      }
    }
    throw new BadGatewayException(`AI ingestion timeout after ${maxWaitMs / 60_000} min`);
  }

  async deleteIngestSource(sourceId: string): Promise<unknown> {
    const headers: Record<string, string> = {};
    if (this.apiKey) headers['X-API-Key'] = this.apiKey;
    if (this.adminToken) headers['X-Admin-Token'] = this.adminToken;
    const res = await fetch(
      `${this.baseUrl}/ingest/source/${encodeURIComponent(sourceId)}`,
      { method: 'DELETE', headers },
    );
    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new BadGatewayException(
        `AI /ingest/source error ${res.status}: ${txt}`,
      );
    }
    return res.json().catch(() => ({}));
  }

  // Helper: convert WHATWG ReadableStream<Uint8Array> to Node Readable.
  static toNodeReadable(stream: ReadableStream<Uint8Array>): Readable {
    return Readable.fromWeb(stream as never);
  }
}
