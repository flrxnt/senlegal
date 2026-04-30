import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import nodemailer, { Transporter } from 'nodemailer';

@Injectable()
export class MailerService implements OnModuleInit {
  private readonly logger = new Logger('MailerService');
  private transporter: Transporter | null = null;
  private from!: string;

  constructor(private readonly config: ConfigService) { }

  onModuleInit() {
    const host = this.config.get<string>('SMTP_HOST');
    this.from = this.config.get<string>('SMTP_FROM') ?? 'SenLégal <no-reply@senlegal.local>';
    if (!host) {
      this.logger.warn('SMTP_HOST not set — emails will only be logged.');
      return;
    }
    const user = this.config.get<string>('SMTP_USER');
    const pass = this.config.get<string>('SMTP_PASS');
    this.transporter = nodemailer.createTransport({
      host,
      port: Number(this.config.get('SMTP_PORT') ?? 1025),
      secure: false,
      auth: user && pass ? { user, pass } : undefined,
    });
  }

  private async send(to: string, subject: string, html: string, text?: string) {
    if (!this.transporter) {
      this.logger.log(`[mail-stub] to=${to} subject="${subject}"`);
      return;
    }
    await this.transporter.sendMail({ from: this.from, to, subject, html, text });
  }

  sendWelcomeEmail(to: string, name?: string | null) {
    const who = name?.trim() || 'cher utilisateur';
    return this.send(
      to,
      'Bienvenue sur SenLégal',
      `<p>Bonjour ${who},</p><p>Votre compte SenLégal a été créé avec succès.</p>`,
      `Bonjour ${who},\nVotre compte SenLégal a été créé.`,
    );
  }

  sendPasswordResetEmail(to: string, resetUrl: string) {
    return this.send(
      to,
      'Réinitialisation de votre mot de passe',
      `<p>Pour réinitialiser votre mot de passe, cliquez ici :</p><p><a href="${resetUrl}">${resetUrl}</a></p><p>Ce lien expire dans 1 heure.</p>`,
      `Réinitialisez votre mot de passe : ${resetUrl}\n(valable 1 heure)`,
    );
  }

  sendSubscriptionActivatedEmail(to: string, plan: string, until: Date) {
    const date = until.toLocaleDateString('fr-FR');
    return this.send(
      to,
      'Abonnement SenLégal activé',
      `<p>Votre abonnement <strong>${plan}</strong> est actif jusqu'au ${date}.</p>`,
    );
  }

  sendSubscriptionExpiredEmail(to: string, plan: string) {
    return this.send(
      to,
      'Votre abonnement SenLégal a expiré',
      `<p>Votre abonnement <strong>${plan}</strong> est arrivé à échéance. Votre compte est repassé en plan FREE.</p>`,
    );
  }

  sendPaymentConfirmationEmail(to: string, amount: number, currency: string) {
    return this.send(
      to,
      'Paiement reçu — SenLégal',
      `<p>Nous avons bien reçu votre paiement de ${amount} ${currency}. Merci !</p>`,
    );
  }

  sendPaymentFailedEmail(to: string) {
    return this.send(
      to,
      'Paiement non abouti — SenLégal',
      `<p>Votre dernier paiement n'a pas pu être traité. Vous pouvez réessayer depuis votre espace.</p>`,
    );
  }
}
