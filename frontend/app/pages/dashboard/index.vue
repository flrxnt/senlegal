<script setup lang="ts">
import { onMounted, computed } from "vue";
import { storeToRefs } from "pinia";
import { useAuthStore } from "~/stores/auth";
import { useChatStore } from "~/stores/chat";
import { useApi } from "~/composables/useApi";
import { planLabel, FREE_DAILY_LIMIT } from "~/utils/plan";

definePageMeta({});
useSeoMeta({ title: "Tableau de bord — SenLégal", robots: "noindex,nofollow" });

const auth = useAuthStore();
const chat = useChatStore();
const { user, isPro } = storeToRefs(auth);
const { conversations } = storeToRefs(chat);

interface UsageQuota {
	dailyMessagesUsed: number;
	dailyMessagesLimit: number | null;
	storageUsedBytes: number;
	storageQuotaBytes: number;
}
const usage = ref<UsageQuota | null>(null);

onMounted(async () => {
	if (!conversations.value.length) await chat.fetchConversations().catch(() => null);
	try {
		usage.value = await useApi()<UsageQuota>("/me/usage");
	} catch {
		usage.value = null;
	}
});

function quotaLabel() {
	if (isPro.value) return "∞";
	if (!usage.value) return `0/${FREE_DAILY_LIMIT}`;
	const limit = usage.value.dailyMessagesLimit ?? FREE_DAILY_LIMIT;
	return `${usage.value.dailyMessagesUsed}/${limit}`;
}

const stats = computed(() => [
	{ label: "Consultations totales", value: conversations.value.length.toString().padStart(2, "0") },
	{ label: "Plan actif", value: planLabel(user.value?.plan).replace("Édition ", "") },
	{ label: "Quota du jour", value: quotaLabel() },
]);
</script>

<template>
	<LayoutDashboardShell>
		<h1 class="font-serif text-4xl md:text-6xl text-ink mb-4">
			Bonjour, <span class="italic font-light text-brand">{{ user?.name?.split(" ")[0] || "Consultant" }}</span
			>.
		</h1>
		<p class="font-sans text-muted-ink font-light text-base md:text-lg max-w-xl mb-12 md:mb-16">
			Votre espace personnel. Retrouvez vos consultations, gérez votre coffre-fort documentaire et ajustez votre abonnement.
		</p>

		<div class="grid sm:grid-cols-3 gap-0 border-t border-b border-rule sm:divide-x divide-rule">
			<div v-for="s in stats" :key="s.label" class="p-6 md:p-8 border-b sm:border-b-0 border-rule">
				<p class="font-sans text-[10px] uppercase tracking-widest text-muted-ink mb-3 font-semibold">{{ s.label }}</p>
				<p class="font-serif text-3xl md:text-4xl text-ink">{{ s.value }}</p>
			</div>
		</div>

		<div class="mt-16 md:mt-20 grid sm:grid-cols-2 gap-6">
			<NuxtLink to="/app" class="border border-ink p-8 hover:bg-ink hover:text-paper transition-colors group">
				<p class="text-[10px] uppercase tracking-widest font-semibold mb-4">Action</p>
				<p class="font-serif text-2xl">Nouvelle consultation →</p>
			</NuxtLink>
			<NuxtLink v-if="!isPro" to="/dashboard/facturation" class="border border-brand text-brand p-8 hover:bg-brand hover:text-paper transition-colors">
				<p class="text-[10px] uppercase tracking-widest font-semibold mb-4">Souscription</p>
				<p class="font-serif text-2xl">Passer à l'édition Cabinet →</p>
			</NuxtLink>
			<NuxtLink v-else to="/dashboard/documents" class="border border-brand text-brand p-8 hover:bg-brand hover:text-paper transition-colors">
				<p class="text-[10px] uppercase tracking-widest font-semibold mb-4">Coffre-fort</p>
				<p class="font-serif text-2xl">Importer un document →</p>
			</NuxtLink>
		</div>
	</LayoutDashboardShell>
</template>
