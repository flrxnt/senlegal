import { Module } from '@nestjs/common';
import { PaymentsService } from './payments.service';
import { PaymentsController } from './payments.controller';
import { PaymentsWebhookController } from './payments-webhook.controller';
import { PaydunyaProvider } from './providers/paydunya.provider';
import { SubscriptionsModule } from '../subscriptions/subscriptions.module';

@Module({
  imports: [SubscriptionsModule],
  controllers: [PaymentsController, PaymentsWebhookController],
  providers: [PaymentsService, PaydunyaProvider],
  exports: [PaymentsService],
})
export class PaymentsModule { }
