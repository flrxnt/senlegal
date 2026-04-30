import { Injectable } from '@nestjs/common';
import { Plan, SubscriptionStatus } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AdminService {
  constructor(private readonly prisma: PrismaService) { }

  async stats() {
    const since = new Date();
    since.setDate(since.getDate() - 30);
    const [users, free, pro, conversations, messages, msgs30d, activeSubs, paidInvoices, errors24h, revenue30d] =
      await this.prisma.$transaction([
        this.prisma.user.count(),
        this.prisma.user.count({ where: { plan: Plan.FREE } }),
        this.prisma.user.count({ where: { plan: Plan.PRO } }),
        this.prisma.conversation.count(),
        this.prisma.message.count(),
        this.prisma.message.count({ where: { createdAt: { gte: since } } }),
        this.prisma.subscription.count({ where: { status: SubscriptionStatus.ACTIVE } }),
        this.prisma.invoice.count({ where: { status: 'PAID' } }),
        this.prisma.errorLog.count({
          where: { createdAt: { gte: new Date(Date.now() - 24 * 3600_000) } },
        }),
        this.prisma.invoice.aggregate({
          _sum: { amount: true },
          where: { status: 'PAID', paidAt: { gte: since } },
        }),
      ]);
    return {
      users,
      usersByPlan: { FREE: free, PRO: pro },
      conversations,
      messages,
      messagesLast30d: msgs30d,
      activeSubscriptions: activeSubs,
      paidInvoices,
      revenueLast30dXof: revenue30d._sum.amount ?? 0,
      errorsLast24h: errors24h,
    };
  }

  async listConversations(opts: { skip?: number; take?: number }) {
    const [items, total] = await this.prisma.$transaction([
      this.prisma.conversation.findMany({
        skip: opts.skip ?? 0,
        take: Math.min(opts.take ?? 50, 200),
        orderBy: { updatedAt: 'desc' },
        include: {
          user: { select: { id: true, email: true, name: true } },
          _count: { select: { messages: true } },
        },
      }),
      this.prisma.conversation.count(),
    ]);
    return { items, total };
  }

  async listInvoices(opts: { skip?: number; take?: number }) {
    const [items, total] = await this.prisma.$transaction([
      this.prisma.invoice.findMany({
        skip: opts.skip ?? 0,
        take: Math.min(opts.take ?? 50, 200),
        orderBy: { createdAt: 'desc' },
        include: { user: { select: { email: true, name: true } } },
      }),
      this.prisma.invoice.count(),
    ]);
    return { items, total };
  }

  async listErrors(opts: { skip?: number; take?: number }) {
    const [items, total] = await this.prisma.$transaction([
      this.prisma.errorLog.findMany({
        skip: opts.skip ?? 0,
        take: Math.min(opts.take ?? 100, 500),
        orderBy: { createdAt: 'desc' },
      }),
      this.prisma.errorLog.count(),
    ]);
    return { items, total };
  }

  async listEvents(opts: { skip?: number; take?: number; type?: string }) {
    const where = opts.type ? { type: opts.type as never } : undefined;
    const [items, total] = await this.prisma.$transaction([
      this.prisma.analyticsEvent.findMany({
        where,
        skip: opts.skip ?? 0,
        take: Math.min(opts.take ?? 100, 500),
        orderBy: { createdAt: 'desc' },
        include: { user: { select: { email: true } } },
      }),
      this.prisma.analyticsEvent.count({ where }),
    ]);
    return { items, total };
  }
}
