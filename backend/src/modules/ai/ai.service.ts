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

  async ingest(buffer: Buffer, filename: string, contentType: string): Promise<unknown> {
    const headers: Record<string, string> = {};
    if (this.apiKey) headers['X-API-Key'] = this.apiKey;
    if (this.adminToken) headers['X-Admin-Token'] = this.adminToken;
    const form = new FormData();
    const blob = new Blob([new Uint8Array(buffer)], { type: contentType });
    form.append('file', blob, filename);
    const res = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      headers,
      body: form as unknown as BodyInit,
    });
    if (!res.ok) {
      const txt = await res.text().catch(() => '');
      throw new BadGatewayException(`AI /ingest error ${res.status}: ${txt}`);
    }
    return res.json().catch(() => ({}));
  }

  // Helper: convert WHATWG ReadableStream<Uint8Array> to Node Readable.
  static toNodeReadable(stream: ReadableStream<Uint8Array>): Readable {
    return Readable.fromWeb(stream as never);
  }
}
