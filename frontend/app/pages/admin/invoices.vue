<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatXof } from "~/utils/plan";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Factures — Admin", robots: "noindex,nofollow" });

interface Invoice {
	id: string;
	provider: string;
	status: string;
	amount: number;
	currency: string;
	createdAt: string;
	user: { email: string; name: string | null };
}

const items = ref<Invoice[]>([]);
const total = ref(0);
const loading = ref(false);
const skip = ref(0);
const take = ref(25);

async function load() {
	loading.value = true;
	try {
		const res = await useApi()<{ items: Invoice[]; total: number }>(`/admin/invoices?skip=${skip.value}&take=${take.value}`);
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
	{ key: "createdAt", label: "Date", span: 3 },
	{ key: "user", label: "Utilisateur", span: 4 },
	{ key: "amount", label: "Montant", span: 2 },
	{ key: "provider", label: "Provider", span: 2 },
	{ key: "status", label: "Statut", span: 1 },
];
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Factures.</h1>
		<p class="text-muted-ink font-light mb-8">{{ total }} transactions enregistrées.</p>

		<AdminDataTable :columns="columns" :rows="items" :loading="loading" :total="total" :skip="skip" :take="take" empty-label="Aucune facture." @update:skip="(v) => (skip = v)">
			<template #createdAt="{ row }">
				<span class="text-[10px] uppercase tracking-widest text-muted-ink">
					{{ new Date(row.createdAt).toLocaleString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }) }}
				</span>
			</template>
			<template #user="{ row }">{{ row.user.email }}</template>
			<template #amount="{ row }"
				><span class="font-serif">{{ formatXof(row.amount) }}</span></template
			>
			<template #provider="{ row }"
				><span class="text-[10px] uppercase tracking-widest">{{ row.provider }}</span></template
			>
			<template #status="{ row }">
				<span
					class="text-[10px] uppercase tracking-widest font-semibold"
					:class="row.status === 'PAID' ? 'text-brand' : row.status === 'FAILED' ? 'text-destructive' : 'text-muted-ink'"
				>
					{{ row.status }}
				</span>
			</template>
		</AdminDataTable>
	</div>
</template>
