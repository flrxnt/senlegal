import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { PrismaService } from '../../prisma/prisma.service';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger('HttpException');

  constructor(private readonly prisma: PrismaService) { }

  async catch(exception: unknown, host: ArgumentsHost): Promise<void> {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const req = ctx.getRequest<Request>();

    const isHttp = exception instanceof HttpException;
    const status = isHttp
      ? (exception as HttpException).getStatus()
      : HttpStatus.INTERNAL_SERVER_ERROR;

    let message: string | object = 'Internal server error';
    if (isHttp) {
      const r = (exception as HttpException).getResponse();
      message = typeof r === 'string' ? r : (r as { message?: string }).message ?? r;
    } else if (exception instanceof Error) {
      message = exception.message;
    }

    if (status >= 500) {
      const err = exception as Error;
      this.logger.error(`${req.method} ${req.url} -> ${status} ${err?.message}`, err?.stack);
      try {
        const userId = (req as Request & { user?: { id?: string } }).user?.id ?? null;
        await this.prisma.errorLog.create({
          data: {
            status,
            message: typeof message === 'string' ? message : JSON.stringify(message),
            stack: err?.stack ?? null,
            path: req.url,
            method: req.method,
            userId,
          },
        });
      } catch (e) {
        this.logger.warn(`Could not persist error log: ${(e as Error).message}`);
      }
    }

    res.status(status).json({
      statusCode: status,
      message,
      timestamp: new Date().toISOString(),
      path: req.url,
    });
  }
}
