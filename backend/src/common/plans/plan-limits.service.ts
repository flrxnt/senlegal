import { ForbiddenException, Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Plan } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';

export interface PlanLimits {
  dailyChatMessages: number; // -1 unlimited
  storageMb: number;
  maxAvatarMb: number;
  maxUserDocumentMb: number;
  maxChatAttachmentMb: number;
}

@Injectable()
export class PlanLimitsService {
  constructor(
    private readonly config: ConfigService,
    private readonly prisma: PrismaService,
  ) { }

  getLimits(plan: Plan): PlanLimits {
    const freeDaily = Number(this.config.get('FREE_DAILY_CHAT_LIMIT') ?? 5);
    const freeStorage = Number(this.config.get('FREE_USER_STORAGE_MB') ?? 50);
    if (plan === Plan.PRO) {
      return {
        dailyChatMessages: -1,
        storageMb: 5_000,
        maxAvatarMb: Number(this.config.get('MAX_AVATAR_SIZE_MB') ?? 2),
        maxUserDocumentMb: Number(this.config.get('MAX_USER_DOCUMENT_SIZE_MB') ?? 25),
        maxChatAttachmentMb: Number(this.config.get('MAX_CHAT_ATTACHMENT_SIZE_MB') ?? 10),
      };
    }
    return {
      dailyChatMessages: freeDaily,
      storageMb: freeStorage,
      maxAvatarMb: Number(this.config.get('MAX_AVATAR_SIZE_MB') ?? 2),
      maxUserDocumentMb: 5,
      maxChatAttachmentMb: 2,
    };
  }

  async assertCanSendChatMessage(userId: string, plan: Plan): Promise<void> {
    const limits = this.getLimits(plan);
    if (limits.dailyChatMessages < 0) return;
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const sent = await this.prisma.message.count({
      where: {
        role: 'USER',
        createdAt: { gte: start },
        conversation: { userId },
      },
    });
    if (sent >= limits.dailyChatMessages) {
      throw new ForbiddenException(
        `Quota gratuit atteint (${limits.dailyChatMessages} messages/jour). Passez à PRO pour continuer.`,
      );
    }
  }

  async assertCanUpload(userId: string, plan: Plan, sizeBytes: number): Promise<void> {
    const limits = this.getLimits(plan);
    const maxBytes = limits.storageMb * 1024 * 1024;
    const agg = await this.prisma.document.aggregate({
      where: { ownerId: userId, kind: { in: ['USER_PRIVATE', 'CHAT_ATTACHMENT', 'AVATAR'] } },
      _sum: { sizeBytes: true },
    });
    const used = agg._sum.sizeBytes ?? 0;
    if (used + sizeBytes > maxBytes) {
      throw new ForbiddenException(
        `Espace de stockage insuffisant (${limits.storageMb} MB). Passez à PRO pour plus d'espace.`,
      );
    }
  }
}
