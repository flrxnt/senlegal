import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  NotFoundException,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { DocumentKind, Plan, Prisma, User, UserRole } from '@prisma/client';
import bcrypt from 'bcrypt';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';
import { PlanLimitsService } from '../../common/plans/plan-limits.service';
import { UpdateProfileDto } from './dto/update-profile.dto';
import { ChangePasswordDto } from './dto/change-password.dto';

const PUBLIC_FIELDS = {
  id: true,
  email: true,
  name: true,
  phone: true,
  role: true,
  plan: true,
  avatarKey: true,
  isActive: true,
  createdAt: true,
  updatedAt: true,
  lastLoginAt: true,
} satisfies Prisma.UserSelect;

@Injectable()
export class UsersService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly storage: StorageService,
    private readonly limits: PlanLimitsService,
    private readonly config: ConfigService,
  ) { }

  private async withAvatarUrl<T extends { avatarKey: string | null }>(u: T) {
    if (!u.avatarKey) return { ...u, avatarUrl: null };
    const url = await this.storage.getSignedDownloadUrl(this.storage.defaultBucket, u.avatarKey);
    return { ...u, avatarUrl: url };
  }

  async getMe(userId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId }, select: PUBLIC_FIELDS });
    if (!user) throw new NotFoundException();
    return this.withAvatarUrl(user);
  }

  async updateMe(userId: string, dto: UpdateProfileDto) {
    const u = await this.prisma.user.update({
      where: { id: userId },
      data: {
        name: dto.name?.trim() ?? undefined,
        phone: dto.phone?.trim() ?? undefined,
      },
      select: PUBLIC_FIELDS,
    });
    return this.withAvatarUrl(u);
  }

  async changePassword(userId: string, dto: ChangePasswordDto) {
    const u = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!u) throw new UnauthorizedException();
    const ok = await bcrypt.compare(dto.currentPassword, u.passwordHash);
    if (!ok) throw new BadRequestException('Mot de passe actuel incorrect.');
    const rounds = Number(this.config.get('BCRYPT_ROUNDS') ?? 12);
    const passwordHash = await bcrypt.hash(dto.newPassword, rounds);
    await this.prisma.user.update({ where: { id: userId }, data: { passwordHash } });
    return { ok: true };
  }

  async uploadAvatar(
    userId: string,
    plan: Plan,
    file: Express.Multer.File,
  ): Promise<{ avatarUrl: string; avatarKey: string }> {
    if (!file) throw new BadRequestException('Aucun fichier fourni.');
    const max = Number(this.config.get('MAX_AVATAR_SIZE_MB') ?? 2) * 1024 * 1024;
    if (file.size > max) throw new BadRequestException('Avatar trop volumineux.');
    if (!file.mimetype.startsWith('image/')) {
      throw new BadRequestException('Le fichier doit être une image.');
    }
    await this.limits.assertCanUpload(userId, plan, file.size);

    const { bucket, key } = await this.storage.upload({
      prefix: `avatars/${userId}`,
      filename: file.originalname,
      contentType: file.mimetype,
      body: file.buffer,
    });

    await this.prisma.$transaction([
      this.prisma.document.create({
        data: {
          ownerId: userId,
          kind: DocumentKind.AVATAR,
          bucket,
          objectKey: key,
          filename: file.originalname,
          contentType: file.mimetype,
          sizeBytes: file.size,
        },
      }),
      this.prisma.user.update({ where: { id: userId }, data: { avatarKey: key } }),
    ]);

    const avatarUrl = await this.storage.getSignedDownloadUrl(bucket, key);
    return { avatarUrl, avatarKey: key };
  }

  // ----- ADMIN -------------------------------------------------------------

  async list(opts: { skip?: number; take?: number; q?: string; plan?: Plan; role?: UserRole }) {
    const where: Prisma.UserWhereInput = {
      ...(opts.plan ? { plan: opts.plan } : {}),
      ...(opts.role ? { role: opts.role } : {}),
      ...(opts.q
        ? {
          OR: [
            { email: { contains: opts.q, mode: 'insensitive' } },
            { name: { contains: opts.q, mode: 'insensitive' } },
          ],
        }
        : {}),
    };
    const [items, total] = await this.prisma.$transaction([
      this.prisma.user.findMany({
        where,
        skip: opts.skip ?? 0,
        take: Math.min(opts.take ?? 50, 200),
        orderBy: { createdAt: 'desc' },
        select: PUBLIC_FIELDS,
      }),
      this.prisma.user.count({ where }),
    ]);
    return { items, total };
  }

  async adminUpdate(
    id: string,
    data: { role?: UserRole; plan?: Plan; isActive?: boolean; name?: string },
  ) {
    return this.prisma.user.update({ where: { id }, data, select: PUBLIC_FIELDS });
  }

  async adminDelete(id: string, currentUserId: string) {
    if (id === currentUserId) {
      throw new ForbiddenException('Vous ne pouvez pas supprimer votre propre compte.');
    }
    await this.prisma.user.delete({ where: { id } });
    return { ok: true };
  }

  async findOrThrow(id: string): Promise<User> {
    const u = await this.prisma.user.findUnique({ where: { id } });
    if (!u) throw new NotFoundException();
    return u;
  }

  /** Compteurs d'usage (messages quotidiens + stockage) pour le tableau de bord. */
  async getUsage(userId: string, plan: Plan) {
    const limits = this.limits.getLimits(plan);
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    const [dailyMessagesUsed, agg] = await this.prisma.$transaction([
      this.prisma.message.count({
        where: { role: 'USER', createdAt: { gte: start }, conversation: { userId } },
      }),
      this.prisma.document.aggregate({
        where: { ownerId: userId, kind: { in: ['USER_PRIVATE', 'CHAT_ATTACHMENT', 'AVATAR'] } },
        _sum: { sizeBytes: true },
      }),
    ]);
    return {
      dailyMessagesUsed,
      dailyMessagesLimit: limits.dailyChatMessages < 0 ? null : limits.dailyChatMessages,
      storageUsedBytes: agg._sum.sizeBytes ?? 0,
      storageQuotaBytes: limits.storageMb * 1024 * 1024,
      maxUserDocumentMb: limits.maxUserDocumentMb,
      maxAvatarMb: limits.maxAvatarMb,
    };
  }
}
