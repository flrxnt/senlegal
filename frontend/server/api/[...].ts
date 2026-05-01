/**
 * Reverse-proxy Nitro : relaie /api/** vers le backend NestJS
 * via le réseau Docker interne (ex. http://backend:3001).
 *
 * Activé uniquement quand NUXT_API_PROXY_TARGET est défini (production).
 * En développement la variable n'est pas positionnée, donc cette route
 * renvoie 404 et le navigateur appelle directement le backend.
 */
export default defineEventHandler((event) => {
  const target = process.env.NUXT_API_PROXY_TARGET
  if (!target) {
    throw createError({ statusCode: 404, statusMessage: 'Not Found' })
  }
  return proxyRequest(event, `${target}${event.path}`)
})
