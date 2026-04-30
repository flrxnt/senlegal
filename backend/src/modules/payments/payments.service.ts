import {
  BadRequestException,
  Injectable,
  Logger,
  NotFoundException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import {
  AnalyticsEventType,
  BillingProvider,
  Invoice,
  InvoiceStatus,
  Plan,
  Prisma,
} from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { PaydunyaProvider, PaydunyaIpnPayload } from './providers/paydunya.provider';
import { SubscriptionsService } from '../subscriptions/subscriptions.service';
import { MailerService } from '../mailer/mailer.service';
import { AnalyticsService } from '../analytics/analytics.service';
import { getPricingFromEnv } from './pricing.config';

@Injectable()
export class PaymentsService {
  private readonly logger = new Logger('PaymentsService');

  constructor(
    private readonly prisma: PrismaService,
    private readonly paydunya: PaydunyaProvider,
    private readonly subs: SubscriptionsService,
    private readonly mailer: MailerService,
    private readonly analytics: AnalyticsService,
    private readonly config: ConfigService,
  ) { }

  async listMyInvoices(userId: string) {
    return this.prisma.invoice.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 100,
    });
  }

  async createCheckout(userId: string, planKey: 'PRO') {
    const pricing = getPricingFromEnv()[planKey];
    if (!pricing) throw new BadRequestException('Plan inconnu.');
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new NotFoundException();

    const baseWeb = this.config.get<string>('WEB_PUBLIC_URL') ?? 'http://localhost:3000';
    const baseApi = this.config.get<string>('APP_PUBLIC_URL') ?? 'http://localhost:3001';

    const invoice = await this.prisma.invoice.create({
      data: {
        userId,
        provider: BillingProvider.PAYDUNYA,
        status: InvoiceStatus.PENDING,
        plan: pricing.plan,
        amount: pricing.amount,
        currency: pricing.currency,
        description: pricing.label,
      },
    });

    const created = await this.paydunya.createCheckoutInvoice({
      totalAmount: pricing.amount,
      description: pricing.label,
      callbackUrl: `${baseApi}/api/payments/webhook/paydunya`,
      cancelUrl: `${baseWeb}/billing/cancel`,
      returnUrl: `${baseWeb}/billing/success?invoice=${invoice.id}`,
      customData: { invoiceId: invoice.id, userId, plan: pricing.plan },
    });

    const updated = await this.prisma.invoice.update({
      where: { id: invoice.id },
      data: {
        providerToken: created.token,
        metadata: created.raw as unknown as Prisma.InputJsonValue,
      },
    });

    return { invoice: updated, checkoutUrl: created.invoiceUrl };
  }

  async handlePaydunyaIpn(payload: PaydunyaIpnPayload) {
    if (!this.paydunya.verifyNotificationHash(payload)) {
      this.logger.warn('PayDunya IPN: invalid hash, ignored.');
      return { ok: false, reason: 'invalid_hash' };
    }
    const token = payload.data?.invoice?.token;
    if (!token) return { ok: false, reason: 'no_token' };
    await this.finalizeFromRemoteByToken(token);
    return { ok: true };
  }

  /** Idempotent finalize using a Postgres advisory lock on the invoice token. */
  async finalizeFromRemoteByToken(token: string): Promise<Invoice | null> {
    const lockKey = this.lockKeyForToken(token);
    return this.prisma.$transaction(async (tx) => {
      // Acquire xact-scoped advisory lock to serialize concurrent IPN/return-url calls
      await tx.$executeRawUnsafe(`SELECT pg_advisory_xact_lock(${lockKey})`);

      const invoice = await tx.invoice.findFirst({ where: { providerToken: token } });
      if (!invoice) {
        this.logger.warn(`finalize: invoice not found for token ${token.slice(0, 8)}…`);
        return null;
      }
      if (invoice.status === InvoiceStatus.PAID) return invoice;

      const remote = await this.paydunya.confirmRemoteInvoice(token);
      if (remote.status !== 'completed') {
        const updated = await tx.invoice.update({
          where: { id: invoice.id },
          data: {
            status: remote.status === 'cancelled' ? InvoiceStatus.CANCELLED : InvoiceStatus.FAILED,
            metadata: remote.raw as unknown as Prisma.InputJsonValue,
          },
        });
        if (updated.status === InvoiceStatus.FAILED) {
          const user = await tx.user.findUnique({ where: { id: updated.userId } });
          if (user) await this.mailer.sendPaymentFailedEmail(user.email).catch(() => { });
          await this.analytics.track(AnalyticsEventType.PAYMENT_FAILED, updated.userId, {}, {
            invoiceId: updated.id,
          });
        }
        return updated;
      }

      // Successful payment: create/renew subscription within same tx.
      const pricing = getPricingFromEnv()[invoice.plan as 'PRO'];
      if (!pricing) throw new Error(`Unknown plan ${invoice.plan} on invoice ${invoice.id}`);

      const sub = await this.subs.createOrRenewTx(tx, {
        userId: invoice.userId,
        plan: pricing.plan,
        amount: invoice.amount,
        currency: invoice.currency,
        provider: BillingProvider.PAYDUNYA,
        durationMonths: pricing.durationMonths,
        invoiceId: invoice.id,
      });

      const finalInvoice = await tx.invoice.update({
        where: { id: invoice.id },
        data: {
          status: InvoiceStatus.PAID,
          paidAt: new Date(),
          subscriptionId: sub.id,
          providerInvoiceId: token,
          metadata: remote.raw as unknown as Prisma.InputJsonValue,
        },
      });

      // Side-effects (out-of-tx) — best-effort.
      const user = await tx.user.findUnique({ where: { id: finalInvoice.userId } });
      if (user) {
        this.mailer
          .sendPaymentConfirmationEmail(user.email, finalInvoice.amount, finalInvoice.currency)
          .catch(() => { });
        this.mailer
          .sendSubscriptionActivatedEmail(user.email, sub.plan, sub.currentPeriodEnd)
          .catch(() => { });
      }
      this.analytics
        .track(AnalyticsEventType.PAYMENT_SUCCEEDED, finalInvoice.userId, {}, {
          invoiceId: finalInvoice.id,
          amount: finalInvoice.amount,
          currency: finalInvoice.currency,
        })
        .catch(() => { });

      return finalInvoice;
    });
  }

  /** Stable signed integer derived from token for advisory lock. */
  private lockKeyForToken(token: string): bigint {
    let h = 0n;
    for (const ch of token) {
      h = (h * 131n + BigInt(ch.charCodeAt(0))) & 0x7fffffffffffffffn;
    }
    return h;
  }

  // Manual reconciliation by user (return URL).
  async reconcileByInvoice(userId: string, invoiceId: string) {
    const inv = await this.prisma.invoice.findUnique({ where: { id: invoiceId } });
    if (!inv || inv.userId !== userId) throw new NotFoundException();
    if (!inv.providerToken) return inv;
    return this.finalizeFromRemoteByToken(inv.providerToken);
  }
}
