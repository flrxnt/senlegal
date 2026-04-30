import { Injectable, Logger } from '@nestjs/common';
import {
  AnalyticsEventType,
  BillingProvider,
  Plan,
  Prisma,
  Subscription,
  SubscriptionStatus,
} from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { MailerService } from '../mailer/mailer.service';
import { AnalyticsService } from '../analytics/analytics.service';

interface CreateOrRenewInput {
  userId: string;
  plan: Plan;
  amount: number;
  currency: string;
  provider: BillingProvider;
  durationMonths: number;
  invoiceId?: string;
}

@Injectable()
export class SubscriptionsService {
  private readonly logger = new Logger('SubscriptionsService');

  constructor(
    private readonly prisma: PrismaService,
    private readonly mailer: MailerService,
    private readonly analytics: AnalyticsService,
  ) { }

  /** Add months to a date, clamping day-of-month. */
  private addMonths(d: Date, months: number): Date {
    const out = new Date(d);
    const day = out.getDate();
    out.setMonth(out.getMonth() + months);
    if (out.getDate() < day) out.setDate(0); // last day of previous month
    return out;
  }

  /**
   * Creates or renews a subscription within an existing transaction.
   * If user already has an ACTIVE subscription on the same plan, extends its currentPeriodEnd.
   */
  async createOrRenewTx(
    tx: Prisma.TransactionClient,
    input: CreateOrRenewInput,
  ): Promise<Subscription> {
    const now = new Date();
    const existing = await tx.subscription.findFirst({
      where: { userId: input.userId, plan: input.plan, status: SubscriptionStatus.ACTIVE },
      orderBy: { currentPeriodEnd: 'desc' },
    });

    let sub: Subscription;
    if (existing) {
      const base = existing.currentPeriodEnd > now ? existing.currentPeriodEnd : now;
      sub = await tx.subscription.update({
        where: { id: existing.id },
        data: {
          currentPeriodEnd: this.addMonths(base, input.durationMonths),
          cancelAtPeriodEnd: false,
          cancelledAt: null,
          amount: input.amount,
          currency: input.currency,
        },
      });
    } else {
      sub = await tx.subscription.create({
        data: {
          userId: input.userId,
          plan: input.plan,
          status: SubscriptionStatus.ACTIVE,
          provider: input.provider,
          amount: input.amount,
          currency: input.currency,
          startedAt: now,
          currentPeriodEnd: this.addMonths(now, input.durationMonths),
        },
      });
    }
    await tx.user.update({ where: { id: input.userId }, data: { plan: input.plan } });
    return sub;
  }

  async cancelAtPeriodEnd(userId: string) {
    const sub = await this.prisma.subscription.findFirst({
      where: { userId, status: SubscriptionStatus.ACTIVE },
      orderBy: { currentPeriodEnd: 'desc' },
    });
    if (!sub) return { ok: true };
    const updated = await this.prisma.subscription.update({
      where: { id: sub.id },
      data: { cancelAtPeriodEnd: true, cancelledAt: new Date() },
    });
    await this.analytics.track(AnalyticsEventType.SUBSCRIPTION_CANCELLED, userId, {}, {
      subscriptionId: updated.id,
    });
    return { ok: true, subscription: updated };
  }

  async listMine(userId: string) {
    return this.prisma.subscription.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
    });
  }

  /**
   * Find ACTIVE subscriptions whose currentPeriodEnd <= `now`,
   * mark them EXPIRED, and downgrade users whose plan is no longer covered.
   */
  async expireDueSubscriptions(now: Date): Promise<{ expired: number; downgraded: number }> {
    const due = await this.prisma.subscription.findMany({
      where: { status: SubscriptionStatus.ACTIVE, currentPeriodEnd: { lte: now } },
      include: { user: { select: { id: true, email: true, plan: true } } },
    });
    let expired = 0;
    let downgraded = 0;
    for (const sub of due) {
      try {
        await this.prisma.$transaction(async (tx) => {
          await tx.subscription.update({
            where: { id: sub.id },
            data: { status: SubscriptionStatus.EXPIRED },
          });
          const stillActive = await tx.subscription.count({
            where: {
              userId: sub.userId,
              status: SubscriptionStatus.ACTIVE,
              currentPeriodEnd: { gt: now },
            },
          });
          if (stillActive === 0 && sub.user.plan !== Plan.FREE) {
            await tx.user.update({ where: { id: sub.userId }, data: { plan: Plan.FREE } });
            downgraded += 1;
          }
        });
        expired += 1;
        await this.analytics.track(AnalyticsEventType.SUBSCRIPTION_EXPIRED, sub.userId, {}, {
          subscriptionId: sub.id,
        });
        await this.mailer.sendSubscriptionExpiredEmail(sub.user.email, sub.plan).catch(() => { });
      } catch (e) {
        this.logger.warn(`expire failed for sub ${sub.id}: ${(e as Error).message}`);
      }
    }
    if (expired > 0) {
      this.logger.log(`Expired ${expired} subscription(s); downgraded ${downgraded} user(s).`);
    }
    return { expired, downgraded };
  }
}
