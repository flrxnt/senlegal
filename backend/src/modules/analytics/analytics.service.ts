import { Injectable, Logger } from '@nestjs/common';
import { AnalyticsEventType, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';

@Injectable()
export class AnalyticsService {
  private readonly logger = new Logger('AnalyticsService');
  constructor(private readonly prisma: PrismaService) { }

  async track(
    type: AnalyticsEventType,
    userId: string | null,
    ctx: { ip?: string; userAgent?: string } = {},
    payload?: Prisma.InputJsonValue,
  ): Promise<void> {
    try {
      await this.prisma.analyticsEvent.create({
        data: {
          type,
          userId: userId ?? null,
          ip: ctx.ip ?? null,
          userAgent: ctx.userAgent ?? null,
          payload: payload ?? Prisma.JsonNull,
        },
      });
    } catch (e) {
      this.logger.warn(`analytics track failed (${type}): ${(e as Error).message}`);
    }
  }
}
