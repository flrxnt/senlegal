<script setup lang="ts">
import { ref, onMounted } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatXof } from "~/utils/plan";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Console admin — SenLégal", robots: "noindex,nofollow" });

interface Stats {
	users: number;
	usersByPlan: { FREE: number; PRO: number };
	conversations: number;
	messages: number;
	messagesLast30d: number;
	activeSubscriptions: number;
	paidInvoices: number;
	revenueLast30dXof: number;
	errorsLast24h: number;
}

const stats = ref<Stats | null>(null);
const loading = ref(true);

onMounted(async () => {
	try {
		stats.value = await useApi()<Stats>("/admin/stats");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Stats indisponibles."));
	} finally {
		loading.value = false;
	}
});
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Vue d'<span class="italic font-light text-brand">ensemble</span>.</h1>
		<p class="text-muted-ink font-light mb-12 max-w-xl">État de la plateforme en temps réel.</p>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-px bg-rule border border-rule">
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Utilisateurs</p>
				<p class="font-serif text-3xl text-ink">{{ stats.users }}</p>
				<p class="text-[10px] text-muted-ink mt-2">{{ stats.usersByPlan.PRO }} PRO · {{ stats.usersByPlan.FREE }} FREE</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Abonnements actifs</p>
				<p class="font-serif text-3xl text-ink">{{ stats.activeSubscriptions }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Conversations</p>
				<p class="font-serif text-3xl text-ink">{{ stats.conversations }}</p>
				<p class="text-[10px] text-muted-ink mt-2">{{ stats.messages }} messages</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Messages (30j)</p>
				<p class="font-serif text-3xl text-ink">{{ stats.messagesLast30d }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Revenus (30j)</p>
				<p class="font-serif text-3xl text-brand">{{ formatXof(stats.revenueLast30dXof) }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Factures payées</p>
				<p class="font-serif text-3xl text-ink">{{ stats.paidInvoices }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Erreurs 24h</p>
				<p class="font-serif text-3xl" :class="stats.errorsLast24h > 0 ? 'text-destructive' : 'text-ink'">{{ stats.errorsLast24h }}</p>
			</div>
		</div>
	</div>
</template>
