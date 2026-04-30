import {
  BadRequestException,
  Controller,
  Delete,
  Get,
  Post,
  Query,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { UserRole } from '@prisma/client';
import { Roles } from '../../common/decorators/roles.decorator';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { BackupService } from './backup.service';

@ApiBearerAuth()
@ApiTags('admin')
@Roles(UserRole.ADMIN)
@Controller('admin/backups')
export class BackupController {
  constructor(private readonly backup: BackupService) { }

  @Get()
  list() {
    return this.backup.listBackups();
  }

  @Post('database')
  createDb() {
    return this.backup.createDatabaseBackup();
  }

  @Post('full')
  createFull(@CurrentUser() user: AuthUser) {
    return this.backup.createFullBackup(user.id);
  }

  @Get('download-url')
  url(@Query('key') key: string) {
    if (!key) throw new BadRequestException('Paramètre key requis.');
    return this.backup.getDownloadUrl(key);
  }

  @Delete()
  remove(@Query('key') key: string) {
    if (!key) throw new BadRequestException('Paramètre key requis.');
    return this.backup.deleteBackup(key);
  }

  @Post('restore')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 2 * 1024 * 1024 * 1024 } }))
  restore(@UploadedFile() file: Express.Multer.File) {
    return this.backup.restoreFromUpload(file);
  }
}
