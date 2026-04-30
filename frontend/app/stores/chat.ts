import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'

export interface Citation {
  article_number: string
  article_title?: string | null
  document: string
  volume?: string | null
  section?: string | null
  page: number
  snippet: string
  score?: number | null
}

export type MessageRole = 'USER' | 'ASSISTANT' | 'SYSTEM'

export interface Message {
  id: string
  role: MessageRole
  content: string
  citations?: Citation[] | null
  usedContext?: boolean
  createdAt: string
  pending?: boolean
  error?: boolean
  /** id local pour les bulles non encore persistées (placeholder pendant le stream). */
  localId?: string
}

export interface ConversationSummary {
  id: string
  title: string
  pinned: boolean
  archived: boolean
  createdAt: string
  updatedAt: string
  _count?: { messages: number }
}

export interface ConversationDetail extends ConversationSummary {
  messages: Message[]
}

function tempId() {
  return 'tmp-' + Math.random().toString(36).slice(2, 10)
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: [] as ConversationSummary[],
    currentId: null as string | null,
    currentMessages: [] as Message[],
    isStreaming: false,
    loadingList: false,
    loadingDetail: false,
  }),

  getters: {
    current(state): ConversationSummary | null {
      return state.conversations.find((c) => c.id === state.currentId) ?? null
    },
  },

  actions: {
    async fetchConversations() {
      const api = useApi()
      this.loadingList = true
      try {
        this.conversations = await api<ConversationSummary[]>('/chat/conversations')
      } finally {
        this.loadingList = false
      }
    },

    async selectConversation(id: string, opts: { force?: boolean } = {}) {
      if (!opts.force && this.currentId === id && this.currentMessages.length > 0) return
      const api = useApi()
      this.loadingDetail = true
      try {
        const conv = await api<ConversationDetail>(`/chat/conversations/${id}`)
        this.currentId = conv.id
        this.currentMessages = conv.messages
        // Met à jour le résumé si déjà présent
        const idx = this.conversations.findIndex((c) => c.id === conv.id)
        if (idx >= 0) {
          const { messages: _omit, ...summary } = conv
          this.conversations[idx] = { ...this.conversations[idx], ...summary }
        }
      } finally {
        this.loadingDetail = false
      }
    },

    async createConversation(title?: string): Promise<ConversationSummary> {
      const api = useApi()
      const conv = await api<ConversationSummary>('/chat/conversations', {
        method: 'POST',
        body: { title },
      })
      this.conversations = [conv, ...this.conversations]
      this.currentId = conv.id
      this.currentMessages = []
      return conv
    },

    async renameConversation(id: string, title: string) {
      const api = useApi()
      const updated = await api<ConversationSummary>(`/chat/conversations/${id}`, {
        method: 'PATCH',
        body: { title },
      })
      this.conversations = this.conversations.map((c) => (c.id === id ? { ...c, ...updated } : c))
    },

    async deleteConversation(id: string) {
      const api = useApi()
      await api(`/chat/conversations/${id}`, { method: 'DELETE' })
      this.conversations = this.conversations.filter((c) => c.id !== id)
      if (this.currentId === id) {
        this.currentId = null
        this.currentMessages = []
      }
    },

    /** Optimistic insertion of the user message before the SSE roundtrip. */
    appendUserMessage(content: string): Message {
      const m: Message = {
        id: tempId(),
        role: 'USER',
        content,
        createdAt: new Date().toISOString(),
        localId: tempId(),
      }
      this.currentMessages.push(m)
      return m
    },

    appendAssistantPlaceholder(): Message {
      const m: Message = {
        id: tempId(),
        role: 'ASSISTANT',
        content: '',
        citations: [],
        createdAt: new Date().toISOString(),
        pending: true,
        localId: tempId(),
      }
      this.currentMessages.push(m)
      return m
    },

    appendToken(localId: string, token: string) {
      const m = this.currentMessages.find((x) => x.localId === localId)
      if (!m) return
      m.content += token
    },

    setCitations(localId: string, citations: Citation[]) {
      const m = this.currentMessages.find((x) => x.localId === localId)
      if (!m) return
      m.citations = citations
    },

    finalizeAssistant(localId: string, opts: { error?: boolean; errorMessage?: string } = {}) {
      const m = this.currentMessages.find((x) => x.localId === localId)
      if (!m) return
      m.pending = false
      if (opts.error) {
        m.error = true
        if (opts.errorMessage) m.content += (m.content ? '\n\n' : '') + `[${opts.errorMessage}]`
      }
    },

    /** Met à jour le résumé local de la conversation (date, titre auto). */
    touchConversation(id: string, patch: Partial<ConversationSummary> = {}) {
      this.conversations = this.conversations.map((c) =>
        c.id === id ? { ...c, ...patch, updatedAt: new Date().toISOString() } : c,
      )
      // Replace en tête (ordre par updatedAt)
      const idx = this.conversations.findIndex((c) => c.id === id)
      if (idx > 0 && !this.conversations[idx]?.pinned) {
        const item = this.conversations.splice(idx, 1)[0]
        if (item) this.conversations.unshift(item)
      }
    },

    /** Applique un titre auto reçu du backend après persistance. */
    applyAutoTitle(id: string, title: string | null) {
      if (!title) return
      this.conversations = this.conversations.map((c) =>
        c.id === id ? { ...c, title } : c,
      )
    },

    reset() {
      this.conversations = []
      this.currentId = null
      this.currentMessages = []
    },
  },
})
