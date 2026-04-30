<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useAuthStore } from "~/stores/auth";
import { useChatStore } from "~/stores/chat";
import { planLabel } from "~/utils/plan";

const auth = useAuthStore();
const chat = useChatStore();
const { user, isAdmin } = storeToRefs(auth);

const items = [
	{ to: "/dashboard", label: "Vue d'ensemble", num: "01" },
	{ to: "/dashboard/historique", label: "Historique", num: "02" },
	{ to: "/dashboard/documents", label: "Coffre-fort", num: "03" },
	{ to: "/dashboard/facturation", label: "Facturation", num: "04" },
	{ to: "/dashboard/compte", label: "Compte", num: "05" },
];

async function logout() {
	await auth.logout();
	chat.reset();
	await navigateTo("/login");
}
</script>

<template>
	<div class="max-w-[1400px] mx-auto px-6 md:px-12 py-12 md:py-20 grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-12 lg:gap-20">
		<aside class="lg:sticky lg:top-12 self-start">
			<div class="font-sans text-[10px] uppercase tracking-[0.3em] text-brand mb-4 font-semibold flex items-center gap-3">
				<span class="w-6 h-px bg-brand" /> Cabinet
			</div>
			<h2 class="font-serif text-3xl md:text-4xl text-ink mb-2">{{ user?.name || user?.email || "Consultant" }}</h2>
			<p class="text-xs uppercase tracking-widest text-muted-ink font-semibold mb-8">{{ planLabel(user?.plan) }}</p>

			<nav class="border-t border-rule">
				<NuxtLink
					v-for="i in items"
					:key="i.to"
					:to="i.to"
					class="flex items-baseline justify-between py-4 border-b border-rule font-sans text-sm uppercase tracking-widest hover:text-brand transition-colors"
					active-class="text-brand"
				>
					<span class="font-serif italic text-base">{{ i.label }}</span>
					<span class="text-[10px] text-muted-ink">{{ i.num }}</span>
				</NuxtLink>
				<NuxtLink
					v-if="isAdmin"
					to="/admin"
					class="flex items-baseline justify-between py-4 border-b border-rule font-sans text-sm uppercase tracking-widest hover:text-brand transition-colors"
					active-class="text-brand"
				>
					<span class="font-serif italic text-base">Console admin</span>
					<span class="text-[10px] text-brand">★</span>
				</NuxtLink>
			</nav>

			<div class="mt-10 flex flex-col gap-4">
				<NuxtLink to="/app" class="text-[10px] uppercase tracking-widest font-semibold text-brand hover:text-brand-dark">→ Nouvelle consultation</NuxtLink>
				<button class="text-left text-[10px] uppercase tracking-widest font-semibold text-muted-ink hover:text-destructive transition-colors" @click="logout">
					← Se déconnecter
				</button>
			</div>
		</aside>

		<section class="min-w-0">
			<slot />
		</section>
	</div>
</template>
