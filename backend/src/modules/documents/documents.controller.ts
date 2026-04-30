import {
  Controller,
  Delete,
  Get,
  Param,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { UserRole } from '@prisma/client';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { Roles } from '../../common/decorators/roles.decorator';
import { DocumentsService } from './documents.service';

@ApiBearerAuth()
@ApiTags('documents')
@Controller()
export class DocumentsController {
  constructor(private readonly docs: DocumentsService) { }

  // --- User -------------------------------------------------------------

  @Get('me/documents')
  listMine(@CurrentUser() user: AuthUser) {
    return this.docs.listMine(user.id);
  }

  @Post('me/documents')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 50 * 1024 * 1024 } }))
  upload(@CurrentUser() user: AuthUser, @UploadedFile() file: Express.Multer.File) {
    return this.docs.uploadMine(user.id, user.plan, file);
  }

  @Get('documents/:id/url')
  url(@Param('id') id: string, @CurrentUser() user: AuthUser) {
    return this.docs.getDownloadUrl(id, user.id, user.role);
  }

  @Delete('me/documents/:id')
  remove(@Param('id') id: string, @CurrentUser() user: AuthUser) {
    return this.docs.deleteMine(id, user.id);
  }

  // --- Admin (RAG sources) ----------------------------------------------

  @Roles(UserRole.ADMIN)
  @Get('admin/rag/sources')
  listRag() {
    return this.docs.listRagSources();
  }

  @Roles(UserRole.ADMIN)
  @Post('admin/rag/sources')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 200 * 1024 * 1024 } }))
  ingestRag(@CurrentUser() user: AuthUser, @UploadedFile() file: Express.Multer.File) {
    return this.docs.ingestRagSource(user.id, file);
  }

  @Roles(UserRole.ADMIN)
  @Delete('admin/rag/sources/:id')
  deleteRag(@Param('id') id: string) {
    return this.docs.deleteRagSource(id);
  }
}
