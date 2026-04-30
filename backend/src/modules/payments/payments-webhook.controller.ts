import { Body, Controller, HttpCode, Post } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { Public } from '../../common/decorators/public.decorator';
import { PaymentsService } from './payments.service';

@ApiTags('payments')
@Controller('payments/webhook')
export class PaymentsWebhookController {
  constructor(private readonly payments: PaymentsService) { }

  @Public()
  @Throttle({ default: { ttl: 60_000, limit: 600 } })
  @HttpCode(200)
  @Post('paydunya')
  async paydunya(@Body() body: unknown) {
    // Handle silently regardless of result; PayDunya retries on non-2xx.
    await this.payments.handlePaydunyaIpn(body as never).catch(() => undefined);
    return { received: true };
  }
}
