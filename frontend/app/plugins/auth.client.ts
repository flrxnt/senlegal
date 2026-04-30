/**
 * Initialise la session côté client le plus tôt possible.
 * S'exécute avant les composants pour éviter le flash "non connecté".
 */
import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async () => {
  const auth = useAuthStore()
  await auth.loadSession()
})
