import {
  BadRequestException,
  ConflictException,
  Injectable,
  Logger,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { AnalyticsEventType, Plan, User, UserRole } from '@prisma/client';
import bcrypt from 'bcrypt';
import { createHash, randomBytes } from 'node:crypto';
import { PrismaService } from '../../prisma/prisma.service';
import { MailerService } from '../mailer/mailer.service';
import { AnalyticsService } from '../analytics/analytics.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { ForgotPasswordDto } from './dto/forgot-password.dto';
import { ResetPasswordDto } from './dto/reset-password.dto';

@Injectable()
export class AuthService {
  private readonly logger = new Logger('AuthService');

  constructor(
    private readonly prisma: PrismaService,
    private readonly jwt: JwtService,
    private readonly config: ConfigService,
    private readonly mailer: MailerService,
    private readonly analytics: AnalyticsService,
  ) { }

  private rounds(): number {
    return Number(this.config.get('BCRYPT_ROUNDS') ?? 12);
  }

  private sign(user: Pick<User, 'id' | 'email' | 'role' | 'plan'>): string {
    return this.jwt.sign({ sub: user.id, email: user.email, role: user.role, plan: user.plan });
  }

  private toPublic(u: User) {
    return {
      id: u.id,
      email: u.email,
      name: u.name,
      phone: u.phone,
      role: u.role,
      plan: u.plan,
      avatarKey: u.avatarKey,
      createdAt: u.createdAt,
      lastLoginAt: u.lastLoginAt,
    };
  }

  async register(dto: RegisterDto, ctx: { ip?: string; userAgent?: string } = {}) {
    const email = dto.email.toLowerCase().trim();
    const existing = await this.prisma.user.findUnique({ where: { email } });
    if (existing) throw new ConflictException('Cet email est déjà utilisé.');

    const passwordHash = await bcrypt.hash(dto.password, this.rounds());
    const user = await this.prisma.user.create({
      data: {
        email,
        passwordHash,
        name: dto.name?.trim() || null,
        phone: dto.phone?.trim() || null,
        role: UserRole.USER,
        plan: Plan.FREE,
      },
    });

    await this.analytics.track(AnalyticsEventType.USER_REGISTERED, user.id, ctx, {
      email: user.email,
    });
    await this.mailer.sendWelcomeEmail(user.email, user.name).catch((e) => {
      this.logger.warn(`welcome email failed: ${(e as Error).message}`);
    });

    return { user: this.toPublic(user), accessToken: this.sign(user) };
  }

  async login(dto: LoginDto, ctx: { ip?: string; userAgent?: string } = {}) {
    const email = dto.email.toLowerCase().trim();
    const user = await this.prisma.user.findUnique({ where: { email } });
    if (!user || !user.isActive) throw new UnauthorizedException('Identifiants invalides.');
    const ok = await bcrypt.compare(dto.password, user.passwordHash);
    if (!ok) throw new UnauthorizedException('Identifiants invalides.');

    await this.prisma.user.update({ where: { id: user.id }, data: { lastLoginAt: new Date() } });
    await this.analytics.track(AnalyticsEventType.USER_LOGGED_IN, user.id, ctx);

    return { user: this.toPublic(user), accessToken: this.sign(user) };
  }

  async me(userId: string) {
    const user = await this.prisma.user.findUnique({ where: { id: userId } });
    if (!user) throw new UnauthorizedException('Utilisateur introuvable.');
    return this.toPublic(user);
  }

  async forgotPassword(dto: ForgotPasswordDto) {
    const email = dto.email.toLowerCase().trim();
    const user = await this.prisma.user.findUnique({ where: { email } });
    // Always return ok to avoid user enumeration.
    if (!user) return { ok: true };

    const token = randomBytes(32).toString('hex');
    const tokenHash = createHash('sha256').update(token).digest('hex');
    const expiresAt = new Date(Date.now() + 1000 * 60 * 60); // 1h

    await this.prisma.passwordResetToken.create({
      data: { userId: user.id, tokenHash, expiresAt },
    });

    const baseUrl = this.config.get<string>('WEB_PUBLIC_URL') ?? 'http://localhost:3000';
    const resetUrl = `${baseUrl}/reset-password?token=${token}`;
    await this.mailer.sendPasswordResetEmail(user.email, resetUrl).catch((e) => {
      this.logger.warn(`reset email failed: ${(e as Error).message}`);
    });

    return { ok: true };
  }

  async resetPassword(dto: ResetPasswordDto) {
    const tokenHash = createHash('sha256').update(dto.token).digest('hex');
    const record = await this.prisma.passwordResetToken.findUnique({ where: { tokenHash } });
    if (!record || record.usedAt || record.expiresAt < new Date()) {
      throw new BadRequestException('Lien expiré ou déjà utilisé.');
    }
    const passwordHash = await bcrypt.hash(dto.password, this.rounds());
    await this.prisma.$transaction([
      this.prisma.user.update({ where: { id: record.userId }, data: { passwordHash } }),
      this.prisma.passwordResetToken.update({
        where: { id: record.id },
        data: { usedAt: new Date() },
      }),
    ]);
    return { ok: true };
  }
}
