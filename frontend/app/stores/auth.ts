import { defineStore } from 'pinia'
import { useApi } from '~/composables/useApi'
import { useAuthToken } from '~/composables/useAuthToken'
import type { Plan, Role } from '~/utils/plan'

export interface AuthUser {
  id: string
  email: string
  name: string | null
  phone: string | null
  role: Role
  plan: Plan
  avatarKey: string | null
  avatarUrl?: string | null
  createdAt: string
  lastLoginAt: string | null
}

interface AuthResponse {
  user: AuthUser
  accessToken: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as AuthUser | null,
    loaded: false,
    loading: false,
  }),
  getters: {
    isAuthenticated: (s) => !!s.user,
    isAdmin: (s) => s.user?.role === 'ADMIN',
    isPro: (s) => s.user?.plan === 'PRO',
  },
  actions: {
    async loadSession(force = false) {
      if (this.loaded && !force) return
      const token = useAuthToken()
      if (!token.value) {
        this.user = null
        this.loaded = true
        return
      }
      try {
        const api = useApi()
        const me = await api<AuthUser>('/auth/me')
        this.user = me
      } catch {
        token.value = null
        this.user = null
      } finally {
        this.loaded = true
      }
    },

    async login(email: string, password: string) {
      const api = useApi()
      this.loading = true
      try {
        const res = await api<AuthResponse>('/auth/login', {
          method: 'POST',
          body: { email, password },
        })
        this.applyAuth(res)
      } finally {
        this.loading = false
      }
    },

    async register(input: { email: string; password: string; name?: string; phone?: string }) {
      const api = useApi()
      this.loading = true
      try {
        const res = await api<AuthResponse>('/auth/register', {
          method: 'POST',
          body: input,
        })
        this.applyAuth(res)
      } finally {
        this.loading = false
      }
    },

    async forgotPassword(email: string) {
      const api = useApi()
      await api('/auth/forgot-password', { method: 'POST', body: { email } })
    },

    async resetPassword(token: string, password: string) {
      const api = useApi()
      await api('/auth/reset-password', { method: 'POST', body: { token, password } })
    },

    applyAuth(res: AuthResponse) {
      const token = useAuthToken()
      token.value = res.accessToken
      this.user = res.user
      this.loaded = true
    },

    setUser(user: AuthUser) {
      this.user = user
    },

    async refreshMe() {
      const api = useApi()
      try {
        this.user = await api<AuthUser>('/auth/me')
      } catch { /* géré par l'intercepteur */ }
    },

    async logout() {
      const token = useAuthToken()
      token.value = null
      this.user = null
      this.loaded = true
    },
  },
})
