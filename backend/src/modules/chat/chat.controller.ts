import {
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  Param,
  Patch,
  Post,
  Req,
  Res,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import type { Request, Response } from 'express';
import { CurrentUser, type AuthUser } from '../../common/decorators/current-user.decorator';
import { ChatService } from './chat.service';
import { AiService, AiCitation } from '../ai/ai.service';
import { PlanLimitsService } from '../../common/plans/plan-limits.service';
import { CreateConversationDto, UpdateConversationDto } from './dto/conversation.dto';
import { SendMessageDto } from './dto/send-message.dto';

@ApiBearerAuth()
@ApiTags('chat')
@Controller('chat')
export class ChatController {
  constructor(
    private readonly chat: ChatService,
    private readonly ai: AiService,
    private readonly limits: PlanLimitsService,
  ) { }

  @Get('conversations')
  list(@CurrentUser() user: AuthUser) {
    return this.chat.listConversations(user.id);
  }

  @Post('conversations')
  create(@CurrentUser() user: AuthUser, @Body() dto: CreateConversationDto) {
    return this.chat.createConversation(user.id, dto.title);
  }

  @Get('conversations/:id')
  read(@CurrentUser() user: AuthUser, @Param('id') id: string) {
    return this.chat.getConversation(user.id, id);
  }

  @Patch('conversations/:id')
  rename(
    @CurrentUser() user: AuthUser,
    @Param('id') id: string,
    @Body() dto: UpdateConversationDto,
  ) {
    return this.chat.renameConversation(user.id, id, dto.title);
  }

  @Delete('conversations/:id')
  remove(@CurrentUser() user: AuthUser, @Param('id') id: string) {
    return this.chat.deleteConversation(user.id, id);
  }

  @Throttle({ default: { ttl: 60_000, limit: 30 } })
  @Post('conversations/:id/messages')
  send(
    @CurrentUser() user: AuthUser,
    @Param('id') id: string,
    @Body() dto: SendMessageDto,
    @Req() req: Request,
  ) {
    return this.chat.sendMessage({
      userId: user.id,
      plan: user.plan,
      conversationId: id,
      question: dto.question,
      topK: dto.topK,
      ip: (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() || req.ip,
      userAgent: req.headers['user-agent'],
    });
  }

  /**
   * Streaming SSE proxy.
   * - validates ownership + quota,
   * - persists user message immediately,
   * - opens upstream SSE to FastAPI,
   * - pipes raw bytes to client while accumulating answer + parsing citations,
   * - persists assistant message at end.
   */
  @Throttle({ default: { ttl: 60_000, limit: 30 } })
  @HttpCode(200)
  @Post('conversations/:id/stream')
  async stream(
    @CurrentUser() user: AuthUser,
    @Param('id') id: string,
    @Body() dto: SendMessageDto,
    @Res() res: Response,
  ) {
    await this.chat.assertOwned(user.id, id);
    await this.limits.assertCanSendChatMessage(user.id, user.plan);

    const history = await this.chat.buildHistory(id);
    await this.chat.createUserMessage(id, dto.question);

    res.status(200);
    res.setHeader('Content-Type', 'text/event-stream; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache, no-transform');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no');
    res.socket?.setNoDelay(true);
    res.flushHeaders?.();

    const writeSse = (event: string, data: string) => {
      res.write(`event: ${event}\n`);
      for (const line of data.split('\n')) res.write(`data: ${line}\n`);
      res.write('\n');
      (res as unknown as { flush?: () => void }).flush?.();
    };

    const upstream = await this.ai.chatStream({
      question: dto.question,
      topK: dto.topK,
      history,
    });

    const reader = (upstream.body as ReadableStream<Uint8Array>).getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let answer = '';
    let citations: AiCitation[] = [];
    let usedContext = false;
    let rewrittenQuestion: string | null = null;
    let currentEvent: string | null = null;
    let dataLines: string[] = [];

    const handleEvent = () => {
      if (!currentEvent) return;
      const data = dataLines.join('\n');
      try {
        if (currentEvent === 'citations') {
          const parsed = JSON.parse(data) as { citations?: AiCitation[]; used_context?: boolean };
          citations = parsed.citations ?? [];
          usedContext = !!parsed.used_context;
        } else if (currentEvent === 'rewritten') {
          const parsed = JSON.parse(data) as { rewritten_question?: string };
          rewrittenQuestion = parsed.rewritten_question?.trim() || null;
        } else if (currentEvent === 'token') {
          answer += data;
        }
      } catch {
        /* ignore malformed event */
      }
      if (currentEvent !== 'done') {
        writeSse(currentEvent, data);
      }
    };

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (!value) continue;
        buffer += decoder.decode(value, { stream: true });
        let idx: number;
        while ((idx = buffer.indexOf('\n')) >= 0) {
          const rawLine = buffer.slice(0, idx).replace(/\r$/, '');
          buffer = buffer.slice(idx + 1);
          if (rawLine === '') {
            handleEvent();
            currentEvent = null;
            dataLines = [];
            continue;
          }
          if (rawLine.startsWith(':')) continue;
          if (rawLine.startsWith('event:')) {
            currentEvent = rawLine.slice(6).trim();
          } else if (rawLine.startsWith('data:')) {
            dataLines.push(rawLine.slice(5).replace(/^ /, ''));
          }
        }
      }
      handleEvent();
    } catch {
      // client probablement deconnecte
    } finally {
      let finalTitle: string | null = null;
      try {
        if (answer.trim().length > 0) {
          const persisted = await this.chat.persistAssistant({
            conversationId: id,
            answer,
            citations,
            usedContext,
            rewrittenQuestion,
            fallbackQuestion: dto.question,
          });
          finalTitle = persisted.title ?? null;
        }
      } catch {
        /* ignore */
      }
      try {
        writeSse('done', JSON.stringify({ conversationId: id, title: finalTitle, rewrittenQuestion }));
      } catch {
        /* ignore */
      }
      res.end();
    }
  }
}
