import { Plan } from '@prisma/client';

export interface CheckoutPlan {
  plan: Plan;
  amount: number;
  currency: string;
  label: string;
  durationMonths: number;
}

export function getPricingFromEnv(): Record<string, CheckoutPlan> {
  const proAmount = Number(process.env.PRICE_PRO_AMOUNT_XOF ?? 9900);
  const proDuration = Number(process.env.PRICE_PRO_DURATION_MONTHS ?? 1);
  return {
    PRO: {
      plan: Plan.PRO,
      amount: proAmount,
      currency: 'XOF',
      label: `SenLégal PRO (${proDuration} mois)`,
      durationMonths: proDuration,
    },
  };
}
