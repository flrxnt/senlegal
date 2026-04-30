import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Cron, CronExpression } from '@nestjs/schedule';
import { SubscriptionsService } from './subscriptions.service';

@Injectable()
export class SubscriptionsScheduler {
  private readonly logger = new Logger('SubscriptionsScheduler');
  private isRunning = false;

  constructor(
    private readonly subs: SubscriptionsService,
    private readonly config: ConfigService,
  ) { }

  @Cron(CronExpression.EVERY_DAY_AT_3AM, { name: 'subscriptions-expire' })
  async runDaily() {
    if ((this.config.get<string>('SUBSCRIPTIONS_SCHEDULER_ENABLED') ?? 'true') !== 'true') {
      return;
    }
    if (this.isRunning) {
      this.logger.warn('Skipped: previous run still in progress.');
      return;
    }
    this.isRunning = true;
    try {
      const r = await this.subs.expireDueSubscriptions(new Date());
      this.logger.log(`cron expire -> expired=${r.expired} downgraded=${r.downgraded}`);
    } catch (e) {
      this.logger.error(`cron expire failed: ${(e as Error).message}`);
    } finally {
      this.isRunning = false;
    }
  }
}
