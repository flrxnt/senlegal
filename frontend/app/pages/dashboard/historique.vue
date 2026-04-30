<script setup lang="ts">
import { onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useChatStore } from "~/stores/chat";

definePageMeta({});
useSeoMeta({ title: "Historique — SenLégal", robots: "noindex,nofollow" });

const chat = useChatStore();
const { conversations, loadingList } = storeToRefs(chat);

onMounted(async () => {
	if (!conversations.value.length) await chat.fetchConversations().catch(() => null);
});

async function open(id: string) {
	await navigateTo({ path: "/app", query: { conv: id } });
}

function format(iso: string) {
	return new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
</script>

<template>
	<LayoutDashboardShell>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-4">Historique <span class="italic font-light text-brand">des consultations</span>.</h1>
		<p class="text-muted-ink font-light mb-12 md:mb-16 max-w-xl">Chaque dossier ouvert avec SenLégal est conservé dans votre archive personnelle.</p>

		<p v-if="loadingList" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!conversations.length" class="border border-rule p-12 text-center">
			<p class="font-serif italic text-2xl text-muted-ink">Aucun dossier pour l'instant.</p>
			<UiButton to="/app" variant="outline" size="md" class="mt-6">Ouvrir une consultation</UiButton>
		</div>

		<ul v-else class="border-t border-rule">
			<li v-for="c in conversations" :key="c.id" class="border-b border-rule">
				<button type="button" class="w-full text-left py-6 grid grid-cols-12 gap-4 items-baseline group hover:bg-paper transition-colors px-2" @click="open(c.id)">
					<span class="col-span-12 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
						{{ format(c.updatedAt) }}
					</span>
					<span class="col-span-9 md:col-span-8 font-serif text-lg md:text-xl text-ink group-hover:text-brand group-hover:italic transition-all truncate">
						{{ c.title || "Nouveau dossier" }}
					</span>
					<span class="col-span-3 md:col-span-2 text-right text-[10px] uppercase tracking-widest text-brand font-semibold"> {{ c._count?.messages ?? 0 }} échanges → </span>
				</button>
			</li>
		</ul>
	</LayoutDashboardShell>
</template>
