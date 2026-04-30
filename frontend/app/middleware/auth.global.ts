import { useAuthStore } from '~/stores/auth'

const PROTECTED = [/^\/app(\/|$)/, /^\/dashboard(\/|$)/, /^\/billing(\/|$)/]
const ADMIN = [/^\/admin(\/|$)/]
const GUEST_ONLY = [/^\/login$/, /^\/forgot-password$/, /^\/reset-password$/]

export default defineNuxtRouteMiddleware(async (to) => {
  if (import.meta.server) return

  const auth = useAuthStore()
  if (!auth.loaded) await auth.loadSession()

  const path = to.path
  const isProtected = PROTECTED.some((r) => r.test(path))
  const isAdminOnly = ADMIN.some((r) => r.test(path))
  const isGuestOnly = GUEST_ONLY.some((r) => r.test(path))

  if ((isProtected || isAdminOnly) && !auth.isAuthenticated) {
    return navigateTo({ path: '/login', query: { next: path } })
  }
  if (isAdminOnly && !auth.isAdmin) {
    return navigateTo('/dashboard')
  }
  if (isGuestOnly && auth.isAuthenticated) {
    return navigateTo('/app')
  }
})
