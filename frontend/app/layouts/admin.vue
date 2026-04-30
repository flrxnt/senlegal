<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useAuthStore } from "~/stores/auth";

const auth = useAuthStore();
const { user } = storeToRefs(auth);

const items = [
	{ to: "/admin", label: "Vue d'ensemble", num: "01" },
	{ to: "/admin/users", label: "Utilisateurs", num: "02" },
	{ to: "/admin/conversations", label: "Conversations", num: "03" },
	{ to: "/admin/invoices", label: "Factures", num: "04" },
	{ to: "/admin/rag", label: "Sources RAG", num: "05" },
	{ to: "/admin/errors", label: "Erreurs", num: "06" },
	{ to: "/admin/events", label: "Événements", num: "07" },
	{ to: "/admin/backups", label: "Sauvegardes", num: "08" },
];

async function logout() {
	await auth.logout();
	await navigateTo("/login");
}
</script>

<template>
	<div class="min-h-screen bg-paper text-ink">
		<div class="max-w-[1480px] mx-auto px-6 md:px-12 py-12 md:py-16 grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-12 lg:gap-16">
			<aside class="lg:sticky lg:top-12 self-start">
				<div class="font-sans text-[10px] uppercase tracking-[0.3em] text-brand mb-4 font-semibold flex items-center gap-3"><span class="w-6 h-px bg-brand" /> Console</div>
				<h2 class="font-serif text-2xl text-ink mb-1">Administration</h2>
				<p class="text-xs uppercase tracking-widest text-muted-ink font-semibold mb-8">{{ user?.email }}</p>

				<nav class="border-t border-rule">
					<NuxtLink
						v-for="i in items"
						:key="i.to"
						:to="i.to"
						class="flex items-baseline justify-between py-3 border-b border-rule font-sans text-sm uppercase tracking-widest hover:text-brand transition-colors"
						:exact-active-class="i.to === '/admin' ? 'text-brand' : ''"
						active-class="text-brand"
					>
						<span class="font-serif italic text-base">{{ i.label }}</span>
						<span class="text-[10px] text-muted-ink">{{ i.num }}</span>
					</NuxtLink>
				</nav>

				<div class="mt-10 flex flex-col gap-4">
					<NuxtLink to="/dashboard" class="text-[10px] uppercase tracking-widest font-semibold text-brand hover:text-brand-dark">→ Espace utilisateur</NuxtLink>
					<button class="text-left text-[10px] uppercase tracking-widest font-semibold text-muted-ink hover:text-destructive transition-colors" @click="logout">
						← Se déconnecter
					</button>
				</div>
			</aside>

			<section class="min-w-0">
				<slot />
			</section>
		</div>
	</div>
</template>
