<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Événements — Admin", robots: "noindex,nofollow" });

interface EventRow {
	id: string;
	type: string;
	createdAt: string;
	payload: unknown;
	user: { email: string } | null;
}

const items = ref<EventRow[]>([]);
const total = ref(0);
const loading = ref(false);
const skip = ref(0);
const take = ref(25);
const typeFilter = ref("");

async function load() {
	loading.value = true;
	try {
		const params = new URLSearchParams();
		params.set("skip", String(skip.value));
		params.set("take", String(take.value));
		if (typeFilter.value) params.set("type", typeFilter.value);
		const res = await useApi()<{ items: EventRow[]; total: number }>(`/admin/events?${params}`);
		items.value = res.items;
		total.value = res.total;
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

watch(skip, load);
let dt: ReturnType<typeof setTimeout> | null = null;
watch(typeFilter, () => {
	if (dt) clearTimeout(dt);
	dt = setTimeout(() => {
		skip.value = 0;
		load();
	}, 250);
});

onMounted(load);

const columns = [
	{ key: "createdAt", label: "Date", span: 3 },
	{ key: "type", label: "Type", span: 3 },
	{ key: "user", label: "Utilisateur", span: 3 },
	{ key: "payload", label: "Payload", span: 3 },
];
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Événements.</h1>
		<p class="text-muted-ink font-light mb-8">{{ total }} événements analytiques.</p>

		<UiInput v-model="typeFilter" placeholder="Filtrer par type (ex. user.signup)" class="mb-6 max-w-sm" />

		<AdminDataTable :columns="columns" :rows="items" :loading="loading" :total="total" :skip="skip" :take="take" empty-label="Aucun événement." @update:skip="(v) => (skip = v)">
			<template #createdAt="{ row }">
				<span class="text-[10px] uppercase tracking-widest text-muted-ink">
					{{ new Date(row.createdAt).toLocaleString("fr-FR") }}
				</span>
			</template>
			<template #type="{ row }">
				<span class="font-mono text-[11px] text-brand">{{ row.type }}</span>
			</template>
			<template #user="{ row }">{{ row.user?.email || "—" }}</template>
			<template #payload="{ row }">
				<span class="text-[10px] text-muted-ink truncate block">{{ JSON.stringify(row.payload) }}</span>
			</template>
		</AdminDataTable>
	</div>
</template>
