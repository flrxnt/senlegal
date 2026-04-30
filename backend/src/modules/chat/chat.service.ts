import {
  ForbiddenException,
  Injectable,
  Logger,
  NotFoundException,
} from '@nestjs/common';
import { AnalyticsEventType, MessageRole, Plan, Prisma } from '@prisma/client';
import { PrismaService } from '../../prisma/prisma.service';
import { AiService, type AiCitation, type AiHistoryMessage } from '../ai/ai.service';
import { PlanLimitsService } from '../../common/plans/plan-limits.service';
import { AnalyticsService } from '../analytics/analytics.service';

const HISTORY_MAX_MESSAGES = 20;

/**
 * Texte exact renvoyé par le service IA quand aucun extrait du Code des marchés
 * publics ne couvre la question. Quand l'IA refuse ainsi, on n'attache aucune
 * citation pour ne pas faire croire à des sources fiables côté UI.
 */
const REFUSAL_TEXT =
  'Je ne dispose pas de cette information dans le Code des marchés publics du Sénégal.';

function isRefusalAnswer(answer: string | null | undefined): boolean {
  if (!answer) return false;
  return answer.trim().replaceAll(/\s+/g, ' ') === REFUSAL_TEXT;
}

@Injectable()
export class ChatService {
  private readonly logger = new Logger('ChatService');

  constructor(
    private readonly prisma: PrismaService,
    private readonly ai: AiService,
    private readonly limits: PlanLimitsService,
    private readonly analytics: AnalyticsService,
  ) { }

  async listConversations(userId: string) {
    return this.prisma.conversation.findMany({
      where: { userId, archived: false },
      orderBy: [{ pinned: 'desc' }, { updatedAt: 'desc' }],
      include: { _count: { select: { messages: true } } },
    });
  }

  async createConversation(userId: string, title?: string) {
    return this.prisma.conversation.create({
      data: { userId, title: title?.trim() || 'Nouvelle conversation' },
    });
  }

  async getConversation(userId: string, id: string) {
    const conv = await this.prisma.conversation.findUnique({
      where: { id },
      include: { messages: { orderBy: { createdAt: 'asc' } } },
    });
    if (!conv || conv.userId !== userId) throw new NotFoundException();
    return conv;
  }

  async renameConversation(userId: string, id: string, title?: string) {
    const conv = await this.prisma.conversation.findUnique({ where: { id } });
    if (!conv || conv.userId !== userId) throw new NotFoundException();
    return this.prisma.conversation.update({
      where: { id },
      data: { title: title?.trim() || conv.title },
    });
  }

  async deleteConversation(userId: string, id: string) {
    const conv = await this.prisma.conversation.findUnique({ where: { id } });
    if (!conv || conv.userId !== userId) throw new NotFoundException();
    await this.prisma.conversation.delete({ where: { id } });
    return { ok: true };
  }

  /** Loads recent messages (oldest first) and converts them to AI history payload. */
  async buildHistory(conversationId: string): Promise<AiHistoryMessage[]> {
    const msgs = await this.prisma.message.findMany({
      where: { conversationId, role: { in: [MessageRole.USER, MessageRole.ASSISTANT] } },
      orderBy: { createdAt: 'desc' },
      take: HISTORY_MAX_MESSAGES,
    });
    return msgs
      .reverse()
      .map((m) => ({
        role: m.role === MessageRole.USER ? 'user' : 'assistant',
        content: m.content,
      }));
  }

  /** Non-streaming chat: persists both user + assistant messages. */
  async sendMessage(opts: {
    userId: string;
    plan: Plan;
    conversationId: string;
    question: string;
    topK?: number;
    ip?: string;
    userAgent?: string;
  }) {
    const { userId, plan, conversationId, question, topK } = opts;
    const conv = await this.assertOwned(userId, conversationId);
    await this.limits.assertCanSendChatMessage(userId, plan);

    const history = await this.buildHistory(conv.id);
    const userMsg = await this.prisma.message.create({
      data: { conversationId: conv.id, role: MessageRole.USER, content: question },
    });

    let response;
    try {
      response = await this.ai.chat({ question, topK, history });
    } catch (e) {
      this.logger.warn(`AI chat failed: ${(e as Error).message}`);
      throw e;
    }

    const refusalAnswer = isRefusalAnswer(response.answer);
    const persistedCitations = refusalAnswer ? [] : response.citations;
    const persistedUsedContext = refusalAnswer ? false : response.used_context;

    const assistantMsg = await this.prisma.message.create({
      data: {
        conversationId: conv.id,
        role: MessageRole.ASSISTANT,
        content: response.answer,
        citations: persistedCitations as unknown as Prisma.InputJsonValue,
        usedContext: persistedUsedContext,
      },
    });
    await this.prisma.conversation.update({
      where: { id: conv.id },
      data: {
        updatedAt: new Date(),
        title: this.maybeAutoTitle(
          conv.title,
          response.rewritten_question || question,
        ),
      },
    });
    await this.analytics.track(
      AnalyticsEventType.CHAT_MESSAGE_SENT,
      userId,
      { ip: opts.ip, userAgent: opts.userAgent },
      { conversationId: conv.id },
    );

    return { userMessage: userMsg, assistantMessage: assistantMsg };
  }

  async assertOwned(userId: string, conversationId: string) {
    const conv = await this.prisma.conversation.findUnique({ where: { id: conversationId } });
    if (!conv || conv.userId !== userId) throw new NotFoundException();
    if (conv.archived) throw new ForbiddenException('Conversation archivée.');
    return conv;
  }

  /** Persist results from a streaming session (called by controller after stream ends). */
  async persistAssistant(opts: {
    conversationId: string;
    answer: string;
    citations: AiCitation[];
    usedContext: boolean;
    rewrittenQuestion?: string | null;
    fallbackQuestion?: string | null;
  }) {
    const refusalAnswer = isRefusalAnswer(opts.answer);
    const persistedCitations = refusalAnswer ? [] : opts.citations;
    const persistedUsedContext = refusalAnswer ? false : opts.usedContext;

    const m = await this.prisma.message.create({
      data: {
        conversationId: opts.conversationId,
        role: MessageRole.ASSISTANT,
        content: opts.answer,
        citations: persistedCitations as unknown as Prisma.InputJsonValue,
        usedContext: persistedUsedContext,
      },
    });
    const conv = await this.prisma.conversation.findUnique({
      where: { id: opts.conversationId },
      select: { title: true },
    });
    const candidate = opts.rewrittenQuestion || opts.fallbackQuestion || '';
    const newTitle = conv ? this.maybeAutoTitle(conv.title, candidate) : undefined;
    const updated = await this.prisma.conversation.update({
      where: { id: opts.conversationId },
      data: { updatedAt: new Date(), ...(newTitle ? { title: newTitle } : {}) },
      select: { title: true },
    });
    return { ...m, title: updated.title };
  }

  async createUserMessage(conversationId: string, content: string) {
    return this.prisma.message.create({
      data: { conversationId, role: MessageRole.USER, content },
    });
  }

  private maybeAutoTitle(current: string, question: string): string | undefined {
    if (current && current !== 'Nouvelle conversation') return undefined;
    const trimmed = question.replace(/\s+/g, ' ').trim();
    if (!trimmed) return undefined;
    return trimmed.length > 60 ? trimmed.slice(0, 57) + '…' : trimmed;
  }
}
