import { Controller, Get, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { SubscriptionsService } from './subscriptions.service';

@ApiBearerAuth()
@ApiTags('subscriptions')
@Controller('me/subscriptions')
export class SubscriptionsController {
  constructor(private readonly subs: SubscriptionsService) { }

  @Get()
  list(@CurrentUser() user: AuthUser) {
    return this.subs.listMine(user.id);
  }

  @Post('cancel')
  cancel(@CurrentUser() user: AuthUser) {
    return this.subs.cancelAtPeriodEnd(user.id);
  }
}
