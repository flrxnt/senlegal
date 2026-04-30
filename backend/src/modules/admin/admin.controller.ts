import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Query,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Plan, UserRole } from '@prisma/client';
import { Roles } from '../../common/decorators/roles.decorator';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { AdminService } from './admin.service';
import { UsersService } from '../users/users.service';

@ApiBearerAuth()
@ApiTags('admin')
@Roles(UserRole.ADMIN)
@Controller('admin')
export class AdminController {
  constructor(
    private readonly admin: AdminService,
    private readonly users: UsersService,
  ) { }

  @Get('stats')
  stats() {
    return this.admin.stats();
  }

  // --- Users ----------------------------------------------------------

  @Get('users')
  listUsers(
    @Query('skip', new ParseIntPipe({ optional: true })) skip?: number,
    @Query('take', new ParseIntPipe({ optional: true })) take?: number,
    @Query('q') q?: string,
    @Query('plan') plan?: Plan,
    @Query('role') role?: UserRole,
  ) {
    return this.users.list({ skip, take, q, plan, role });
  }

  @Patch('users/:id')
  updateUser(
    @Param('id') id: string,
    @Body()
    dto: { role?: UserRole; plan?: Plan; isActive?: boolean; name?: string },
  ) {
    return this.users.adminUpdate(id, dto);
  }

  @Delete('users/:id')
  deleteUser(@Param('id') id: string, @CurrentUser() user: AuthUser) {
    return this.users.adminDelete(id, user.id);
  }

  // --- Conversations / Invoices / Logs --------------------------------

  @Get('conversations')
  listConv(
    @Query('skip', new ParseIntPipe({ optional: true })) skip?: number,
    @Query('take', new ParseIntPipe({ optional: true })) take?: number,
  ) {
    return this.admin.listConversations({ skip, take });
  }

  @Get('invoices')
  listInv(
    @Query('skip', new ParseIntPipe({ optional: true })) skip?: number,
    @Query('take', new ParseIntPipe({ optional: true })) take?: number,
  ) {
    return this.admin.listInvoices({ skip, take });
  }

  @Get('errors')
  listErrors(
    @Query('skip', new ParseIntPipe({ optional: true })) skip?: number,
    @Query('take', new ParseIntPipe({ optional: true })) take?: number,
  ) {
    return this.admin.listErrors({ skip, take });
  }

  @Get('events')
  listEvents(
    @Query('skip', new ParseIntPipe({ optional: true })) skip?: number,
    @Query('take', new ParseIntPipe({ optional: true })) take?: number,
    @Query('type') type?: string,
  ) {
    return this.admin.listEvents({ skip, take, type });
  }
}
