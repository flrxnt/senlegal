<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatXof, planLabel, planTagline } from "~/utils/plan";

definePageMeta({});
useSeoMeta({ title: "Facturation — SenLégal", robots: "noindex,nofollow" });

const auth = useAuthStore();
const { user, isPro } = storeToRefs(auth);

interface Invoice {
	id: string;
	provider: string;
	status: string;
	amount: number;
	currency: string;
	createdAt: string;
	paidAt: string | null;
}
interface Subscription {
	id: string;
	plan: "FREE" | "PRO";
	status: string;
	currentPeriodEnd: string | null;
	cancelAtPeriodEnd: boolean;
	createdAt: string;
}

const invoices = ref<Invoice[]>([]);
const subscriptions = ref<Subscription[]>([]);
const loading = ref(true);
const submitting = ref(false);

async function refresh() {
	loading.value = true;
	try {
		const [inv, subs] = await Promise.all([useApi()<Invoice[]>("/payments/me/invoices"), useApi()<Subscription[]>("/me/subscriptions")]);
		invoices.value = inv;
		subscriptions.value = subs;
	} catch (e) {
		toast.error(apiErrorMessage(e, "Impossible de charger la facturation."));
	} finally {
		loading.value = false;
	}
}

onMounted(refresh);

const activeSubscription = computed(() => subscriptions.value.find((s) => s.status === "ACTIVE" && s.plan === "PRO"));

async function upgrade() {
	submitting.value = true;
	try {
		const res = await useApi()<{ checkoutUrl: string }>("/payments/checkout", {
			method: "POST",
			body: { plan: "PRO" },
		});
		if (res?.checkoutUrl) {
			globalThis.location.href = res.checkoutUrl;
		} else {
			toast.error("Lien de paiement indisponible.");
		}
	} catch (e) {
		toast.error(apiErrorMessage(e, "Création du paiement impossible."));
	} finally {
		submitting.value = false;
	}
}

async function cancel() {
	if (!globalThis.confirm("Confirmer l'annulation à la fin de la période en cours ?")) return;
	try {
		await useApi()("/me/subscriptions/cancel", { method: "POST" });
		toast.success("Abonnement annulé en fin de période.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Annulation impossible."));
	}
}

function statusLabel(s: string) {
	const map: Record<string, string> = {
		PAID: "Payée",
		PENDING: "En attente",
		FAILED: "Échec",
		REFUNDED: "Remboursée",
		CANCELLED: "Annulée",
		ACTIVE: "Actif",
		EXPIRED: "Expiré",
	};
	return map[s] || s;
}
</script>

<template>
	<LayoutDashboardShell>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-4">Facturation <span class="italic font-light text-brand">& abonnement</span>.</h1>
		<p class="text-muted-ink font-light mb-12 md:mb-16 max-w-xl">Gérez votre plan et vos modes de paiement. Vous pouvez changer de formule à tout moment.</p>

		<div class="grid grid-cols-1 md:grid-cols-2 gap-0 border-t border-b border-rule md:divide-x divide-rule">
			<div class="p-8 md:p-12">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Plan actuel</p>
				<h2 class="font-serif text-3xl text-ink mb-2">{{ planLabel(user?.plan) }}</h2>
				<p class="text-sm text-muted-ink font-light">{{ planTagline(user?.plan) }}</p>
				<div v-if="activeSubscription" class="mt-6 text-[10px] uppercase tracking-widest text-muted-ink space-y-1">
					<p v-if="activeSubscription.currentPeriodEnd">
						Échéance : {{ new Date(activeSubscription.currentPeriodEnd).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" }) }}
					</p>
					<p v-if="activeSubscription.cancelAtPeriodEnd" class="text-destructive">Annulation programmée en fin de période.</p>
				</div>
				<button
					v-if="activeSubscription && !activeSubscription.cancelAtPeriodEnd"
					class="mt-6 text-[10px] uppercase tracking-widest font-semibold text-destructive border-b border-destructive pb-1 hover:opacity-80"
					@click="cancel"
				>
					Annuler l'abonnement
				</button>
			</div>

			<div v-if="!isPro" class="p-8 md:p-12 bg-brand text-paper">
				<p class="text-[10px] uppercase tracking-widest text-paper/70 font-semibold mb-3">Recommandation</p>
				<h2 class="font-serif text-3xl text-white mb-2">Passez à Cabinet.</h2>
				<p class="text-sm text-paper/90 font-light mb-8">{{ formatXof(9900) }} / mois — consultations illimitées et coffre-fort 5 Go.</p>
				<button
					class="border border-paper text-paper px-6 py-3 text-xs uppercase tracking-widest font-semibold hover:bg-paper hover:text-brand transition-colors disabled:opacity-50"
					:disabled="submitting"
					@click="upgrade"
				>
					{{ submitting ? "Préparation…" : "Souscrire au plan" }}
				</button>
				<p class="text-[10px] text-paper/70 mt-4">Paiement sécurisé via PayDunya (Mobile Money, Wave, carte).</p>
			</div>
			<div v-else class="p-8 md:p-12 bg-paper">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Statut</p>
				<h2 class="font-serif text-3xl text-ink mb-2">Cabinet actif.</h2>
				<p class="text-sm text-muted-ink font-light">Merci de votre confiance. Bonnes consultations.</p>
			</div>
		</div>

		<div class="mt-16">
			<h3 class="font-serif text-2xl text-ink mb-6">Historique de facturation</h3>
			<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>
			<p v-else-if="!invoices.length" class="text-muted-ink text-sm font-light italic border border-rule p-8 text-center">Aucune facture pour le moment.</p>
			<ul v-else class="border-t border-rule">
				<li v-for="inv in invoices" :key="inv.id" class="border-b border-rule py-4 grid grid-cols-12 gap-4 items-center px-2">
					<span class="col-span-6 md:col-span-3 text-[10px] uppercase tracking-widest text-muted-ink">
						{{ new Date(inv.createdAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" }) }}
					</span>
					<span class="col-span-6 md:col-span-3 font-serif text-base text-ink">{{ formatXof(inv.amount) }}</span>
					<span class="col-span-6 md:col-span-3 text-[10px] uppercase tracking-widest text-muted-ink">{{ inv.provider }}</span>
					<span
						class="col-span-6 md:col-span-3 text-[10px] uppercase tracking-widest font-semibold"
						:class="inv.status === 'PAID' ? 'text-brand' : inv.status === 'FAILED' ? 'text-destructive' : 'text-muted-ink'"
					>
						{{ statusLabel(inv.status) }}
					</span>
				</li>
			</ul>
		</div>
	</LayoutDashboardShell>
</template>
