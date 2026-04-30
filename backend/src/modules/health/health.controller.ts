import { Controller, Get } from '@nestjs/common';
import { ApiTags } from '@nestjs/swagger';
import { Public } from '../../common/decorators/public.decorator';
import { PrismaService } from '../../prisma/prisma.service';
import { StorageService } from '../storage/storage.service';

@ApiTags('health')
@Controller('health')
export class HealthController {
  constructor(
    private readonly prisma: PrismaService,
    private readonly storage: StorageService,
  ) { }

  @Public()
  @Get()
  async health() {
    let db = false;
    let s3 = false;
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      db = true;
    } catch {
      /* ignore */
    }
    try {
      await this.storage.ensureBucket(this.storage.defaultBucket);
      s3 = true;
    } catch {
      /* ignore */
    }
    return {
      status: db && s3 ? 'ok' : 'degraded',
      db,
      s3,
      time: new Date().toISOString(),
    };
  }
}
