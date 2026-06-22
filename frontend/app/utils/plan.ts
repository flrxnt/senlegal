/**
 * Helpers de présentation des plans backend (FREE / PRO).
 * On garde un libellé éditorial pour rester dans le ton.
 */
export type Plan = 'FREE' | 'PRO'
export type Role = 'USER' | 'ADMIN'

export function planLabel(plan: Plan | null | undefined): string {
  return plan === 'PRO' ? 'Édition Cabinet' : 'Édition Découverte'
}

export function planTagline(plan: Plan | null | undefined): string {
  return plan === 'PRO'
    ? 'Consultations illimitées, corpus juridique complet, analyses approfondies.'
    : '5 consultations par jour, accès intégral au Code de la Famille.'
}

export const FREE_DAILY_LIMIT = 5
export const FREE_STORAGE_MB = 50
export const PRO_STORAGE_MB = 5_000

/** Formatte des octets en libellé court (ex: "12.4 MB"). */
export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(1)} Ko`
  const mb = kb / 1024
  if (mb < 1024) return `${mb.toFixed(1)} Mo`
  return `${(mb / 1024).toFixed(2)} Go`
}

/** Formatte un montant XOF (centimes non utilisés côté backend, valeur entière). */
export function formatXof(amount: number): string {
  return `${new Intl.NumberFormat('fr-FR').format(amount)} FCFA`
}
