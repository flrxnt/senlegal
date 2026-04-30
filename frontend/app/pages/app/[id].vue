<script setup lang="ts">
import { useChatStore } from "~/stores/chat";

definePageMeta({ layout: "app" });
useSeoMeta({ title: "Consultation — SenLégal", robots: "noindex,nofollow" });

const route = useRoute();
const router = useRouter();
const chat = useChatStore();

// Délègue le rendu à la page index en fixant la conversation courante.
onMounted(async () => {
	const id = route.params.id as string;
	if (!chat.conversations.length) await chat.fetchConversations();
	try {
		await chat.selectConversation(id);
	} catch {
		await router.replace("/app");
		return;
	}
	await router.replace({ path: "/app", query: { conv: id } });
});
</script>

<template>
	<div class="flex items-center justify-center h-full text-muted-ink text-xs uppercase tracking-widest">Chargement…</div>
</template>
