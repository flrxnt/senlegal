import 'dotenv/config';
import { NestFactory } from '@nestjs/core';
import { AppModule } from '../src/app.module';
import { SubscriptionsService } from '../src/modules/subscriptions/subscriptions.service';

async function main() {
  const app = await NestFactory.createApplicationContext(AppModule, {
    logger: ['error', 'warn', 'log'],
  });
  const subs = app.get(SubscriptionsService);
  const result = await subs.expireDueSubscriptions(new Date());
  console.log(`[expire-subscriptions] expired=${result.expired} downgraded=${result.downgraded}`);
  await app.close();
}

main().catch((err) => {
  console.error('[expire-subscriptions] failed', err);
  process.exit(1);
});
