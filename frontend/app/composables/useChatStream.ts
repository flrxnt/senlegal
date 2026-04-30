import type { Citation } from '~/stores/chat'
import { useAuthToken } from '~/composables/useAuthToken'

export interface StreamDoneInfo {
  conversationId: string
  title: string | null
  rewrittenQuestion: string | null
}

export interface StreamHandlers {
  onCitations?: (citations: Citation[], usedContext: boolean) => void
  onToken?: (token: string) => void
  onDone?: (info: StreamDoneInfo | null) => void
  onError?: (err: Error) => void
}

/**
 * Consomme le flux SSE du backend NestJS (POST /chat/conversations/:id/stream).
 * Le backend forward fidèlement les frames SSE de la couche AI :
 *   event: citations \n data: {"citations":[...], "used_context":true} \n\n
 *   event: token     \n data: <chunk>                                  \n\n
 *   event: done      \n data: ok                                       \n\n
 */
export function useChatStream() {
  let controller: AbortController | null = null

  async function send(
    conversationId: string,
    question: string,
    handlers: StreamHandlers = {},
    opts: { topK?: number } = {},
  ) {
    controller?.abort()
    controller = new AbortController()
    const token = useAuthToken()
    const config = useRuntimeConfig()
    const base = (config.public.apiBase as string).replace(/\/$/, '')

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      }
      if (token.value) headers.Authorization = `Bearer ${token.value}`

      const res = await fetch(`${base}/chat/conversations/${conversationId}/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ question, topK: opts.topK }),
        signal: controller.signal,
      })

      if (res.status === 401) {
        token.value = null
        throw new Error('Session expirée. Veuillez vous reconnecter.')
      }
      if (res.status === 403) {
        throw new Error('Quota atteint. Passez à l’édition Cabinet pour continuer.')
      }
      if (!res.ok || !res.body) {
        throw new Error(`Échec de la consultation (HTTP ${res.status}).`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const frames = buffer.split(/\r?\n\r?\n/)
        buffer = frames.pop() ?? ''
        for (const frame of frames) {
          if (!frame.trim()) continue
          let event = 'message'
          const dataLines: string[] = []
          for (const line of frame.split(/\r?\n/)) {
            if (line.startsWith('event:')) event = line.slice(6).trim()
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
          }
          const data = dataLines.join('\n')
          if (event === 'citations') {
            try {
              const parsed = JSON.parse(data) as { citations?: Citation[]; used_context?: boolean }
              handlers.onCitations?.(parsed.citations || [], !!parsed.used_context)
            } catch {
              /* malformed */
            }
          } else if (event === 'token') {
            handlers.onToken?.(data)
          } else if (event === 'done') {
            let info: StreamDoneInfo | null = null
            try {
              info = JSON.parse(data) as StreamDoneInfo
            } catch {
              /* old format: data === 'ok' */
            }
            handlers.onDone?.(info)
            return
          }
        }
      }
      handlers.onDone?.(null)
    } catch (err: unknown) {
      if ((err as Error)?.name === 'AbortError') return
      handlers.onError?.(err as Error)
    } finally {
      controller = null
    }
  }

  function abort() {
    controller?.abort()
    controller = null
  }

  return { send, abort }
}
