import type { FetchError } from 'ofetch'

/**
 * Client HTTP central qui parle au backend NestJS.
 *
 * - Préfixe systhmatiquement `baseURL` (ex: http://localhost:3001/api).
 * - Injecte `Authorization: Bearer <token>` si présent.
 * - Sur 401, purge la session et redirige vers /login (sauf endpoints publics).
 */
type ApiClient = ReturnType<typeof $fetch.create>
let _api: ApiClient | null = null

export function useApi(): ApiClient {
  if (_api) return _api
  const config = useRuntimeConfig()
  const token = useAuthToken()

  const client = $fetch.create({
    baseURL: config.public.apiBase,
    onRequest({ options }) {
      if (token.value) {
        options.headers = new Headers(options.headers)
        options.headers.set('Authorization', `Bearer ${token.value}`)
      }
    },
    async onResponseError({ response, request }) {
      if (response.status === 401) {
        const url = String(request)
        const isPublic =
          url.includes('/auth/login') ||
          url.includes('/auth/register') ||
          url.includes('/auth/forgot-password') ||
          url.includes('/auth/reset-password')
        if (!isPublic) {
          token.value = null
          if (import.meta.client) {
            const route = useRoute()
            const next = route.fullPath
            await navigateTo({ path: '/login', query: next ? { next } : undefined })
          }
        }
      }
    },
  })
  _api = client
  return client
}

export type ApiError = FetchError

/** Extrait un message d'erreur lisible depuis une erreur de fetch. */
export function apiErrorMessage(err: unknown, fallback = 'Une erreur est survenue.'): string {
  const e = err as ApiError | undefined
  const data = e?.data as { message?: string | string[]; error?: string } | undefined
  const m = data?.message
  if (Array.isArray(m)) return m[0] ?? fallback
  if (typeof m === 'string' && m.length > 0) return m
  if (typeof data?.error === 'string') return data.error
  return e?.message || fallback
}
