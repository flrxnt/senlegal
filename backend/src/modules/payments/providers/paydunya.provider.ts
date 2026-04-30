import { BadGatewayException, Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { createHash } from 'node:crypto';

export interface CreateInvoiceInput {
  totalAmount: number;
  description: string;
  callbackUrl: string;
  cancelUrl: string;
  returnUrl: string;
  customData?: Record<string, string>;
}

export interface CreateInvoiceResult {
  token: string;
  invoiceUrl: string;
  raw: unknown;
}

export interface PaydunyaIpnPayload {
  hash?: string;
  data?: {
    invoice?: {
      token?: string;
      total_amount?: number;
      status?: string;
    };
    response_code?: string;
    response_text?: string;
    custom_data?: Record<string, string>;
  };
}

@Injectable()
export class PaydunyaProvider {
  private readonly logger = new Logger('PaydunyaProvider');

  constructor(private readonly config: ConfigService) { }

  private headers() {
    const masterKey = this.config.get<string>('PAYDUNYA_MASTER_KEY') ?? '';
    const privateKey = this.config.get<string>('PAYDUNYA_PRIVATE_KEY') ?? '';
    const token = this.config.get<string>('PAYDUNYA_TOKEN') ?? '';
    return {
      'Content-Type': 'application/json',
      'PAYDUNYA-MASTER-KEY': masterKey,
      'PAYDUNYA-PRIVATE-KEY': privateKey,
      'PAYDUNYA-TOKEN': token,
    };
  }

  private baseUrl(): string {
    const mode = (this.config.get<string>('PAYDUNYA_MODE') ?? 'test').toLowerCase();
    return mode === 'live'
      ? 'https://app.paydunya.com/api/v1'
      : 'https://app.paydunya.com/sandbox-api/v1';
  }

  isConfigured(): boolean {
    return !!(
      this.config.get('PAYDUNYA_MASTER_KEY') &&
      this.config.get('PAYDUNYA_PRIVATE_KEY') &&
      this.config.get('PAYDUNYA_TOKEN')
    );
  }

  async createCheckoutInvoice(input: CreateInvoiceInput): Promise<CreateInvoiceResult> {
    if (!this.isConfigured()) {
      throw new BadGatewayException('PayDunya non configuré.');
    }
    const body = {
      invoice: {
        total_amount: input.totalAmount,
        description: input.description,
      },
      store: {
        name: this.config.get<string>('PAYDUNYA_STORE_NAME') ?? 'SenLégal',
        logo_url: this.config.get<string>('PAYDUNYA_STORE_LOGO_URL') || undefined,
        website_url: this.config.get<string>('PAYDUNYA_STORE_WEBSITE_URL') || undefined,
      },
      actions: {
        callback_url: input.callbackUrl,
        cancel_url: input.cancelUrl,
        return_url: input.returnUrl,
      },
      custom_data: input.customData ?? {},
    };

    const res = await fetch(`${this.baseUrl()}/checkout-invoice/create`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    const json = (await res.json().catch(() => ({}))) as {
      response_code?: string;
      response_text?: string;
      token?: string;
      invoice_url?: string;
      message?: string;
    };
    if (!res.ok || json.response_code !== '00' || !json.token) {
      throw new BadGatewayException(
        `PayDunya create error: ${json.response_text ?? json.message ?? res.status}`,
      );
    }
    return { token: json.token, invoiceUrl: json.invoice_url ?? '', raw: json };
  }

  async confirmRemoteInvoice(token: string): Promise<{
    status: string;
    totalAmount: number;
    customData?: Record<string, string>;
    raw: unknown;
  }> {
    const res = await fetch(`${this.baseUrl()}/checkout-invoice/confirm/${token}`, {
      method: 'GET',
      headers: this.headers(),
    });
    const json = (await res.json().catch(() => ({}))) as {
      response_code?: string;
      status?: string;
      invoice?: { total_amount?: number };
      custom_data?: Record<string, string>;
    };
    if (!res.ok || json.response_code !== '00') {
      throw new BadGatewayException(`PayDunya confirm error: ${res.status}`);
    }
    return {
      status: (json.status ?? 'cancelled').toLowerCase(),
      totalAmount: Number(json.invoice?.total_amount ?? 0),
      customData: json.custom_data,
      raw: json,
    };
  }

  /**
   * Verifies the IPN hash. PayDunya signs payloads with sha512(masterKey).
   */
  verifyNotificationHash(payload: PaydunyaIpnPayload): boolean {
    const masterKey = this.config.get<string>('PAYDUNYA_MASTER_KEY') ?? '';
    if (!payload?.hash || !masterKey) return false;
    const expected = createHash('sha512').update(masterKey, 'utf8').digest('hex');
    return expected === payload.hash;
  }
}
