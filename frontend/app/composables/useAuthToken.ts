/**
 * Cookie typé qui stocke le JWT du backend SenLégal.
 *
 * Choix : `httpOnly: false` car le token doit être lisible en JS pour
 * être envoyé en header Authorization sur les requêtes SSE (le backend
 * ne lit pas le cookie pour l'auth, il attend un Bearer).
 * Mitigations : Helmet côté backend + CSP front + SameSite=lax.
 */
export function useAuthToken() {
  return useCookie<string | null>('senlegal_token', {
    default: () => null,
    sameSite: 'lax',
    secure: !import.meta.dev,
    maxAge: 60 * 60 * 24 * 7, // 7 jours (alignés sur JWT_EXPIRES_IN backend)
    path: '/',
  })
}
