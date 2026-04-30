<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Conversations — Admin", robots: "noindex,nofollow" });

interface Row {
	id: string;
	title: string | null;
	updatedAt: string;
	user: { id: string; email: string; name: string | null };
	_count: { messages: number };
}

const items = ref<Row[]>([]);
const total = ref(0);
const loading = ref(false);
const skip = ref(0);
const take = ref(25);

async function load() {
	loading.value = true;
	try {
		const res = await useApi()<{ items: Row[]; total: number }>(`/admin/conversations?skip=${skip.value}&take=${take.value}`);
		items.value = res.items;
		total.value = res.total;
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

watch(skip, load);
onMounted(load);

const columns = [
	{ key: "updatedAt", label: "Date", span: 3 },
	{ key: "user", label: "Utilisateur", span: 4 },
	{ key: "title", label: "Titre", span: 4 },
	{ key: "count", label: "Messages", span: 1 },
];

function fmt(iso: string) {
	return new Date(iso).toLocaleString("fr-FR", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Conversations.</h1>
		<p class="text-muted-ink font-light mb-8">{{ total }} dossiers enregistrés.</p>

		<AdminDataTable
			:columns="columns"
			:rows="items"
			:loading="loading"
			:total="total"
			:skip="skip"
			:take="take"
			empty-label="Aucune conversation."
			@update:skip="(v) => (skip = v)"
		>
			<template #updatedAt="{ row }">
				<span class="text-[10px] uppercase tracking-widest text-muted-ink">{{ fmt(row.updatedAt) }}</span>
			</template>
			<template #user="{ row }">
				<span class="text-ink">{{ row.user.email }}</span>
			</template>
			<template #title="{ row }">
				<span class="font-serif italic">{{ row.title || "Nouveau dossier" }}</span>
			</template>
			<template #count="{ row }">
				<span class="text-brand font-semibold">{{ row._count.messages }}</span>
			</template>
		</AdminDataTable>
	</div>
</template>
