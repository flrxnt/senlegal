import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { PaymentsService } from './payments.service';
import { CreateCheckoutDto } from './dto/create-checkout.dto';

@ApiBearerAuth()
@ApiTags('payments')
@Controller('payments')
export class PaymentsController {
  constructor(private readonly payments: PaymentsService) { }

  @Post('checkout')
  checkout(@CurrentUser() user: AuthUser, @Body() dto: CreateCheckoutDto) {
    return this.payments.createCheckout(user.id, dto.plan);
  }

  @Post('reconcile/:invoiceId')
  reconcile(@CurrentUser() user: AuthUser, @Param('invoiceId') invoiceId: string) {
    return this.payments.reconcileByInvoice(user.id, invoiceId);
  }

  @Get('me/invoices')
  myInvoices(@CurrentUser() user: AuthUser) {
    return this.payments.listMyInvoices(user.id);
  }
}
