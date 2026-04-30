<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Erreurs — Admin", robots: "noindex,nofollow" });

interface ErrorRow {
	id: string;
	level: string;
	message: string;
	stack: string | null;
	context: unknown;
	createdAt: string;
	userId: string | null;
}

const items = ref<ErrorRow[]>([]);
const total = ref(0);
const loading = ref(false);
const skip = ref(0);
const take = ref(25);
const opened = ref<string | null>(null);

async function load() {
	loading.value = true;
	try {
		const res = await useApi()<{ items: ErrorRow[]; total: number }>(`/admin/errors?skip=${skip.value}&take=${take.value}`);
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

function toggle(id: string) {
	opened.value = opened.value === id ? null : id;
}
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Erreurs <span class="italic font-light text-destructive">remontées</span>.</h1>
		<p class="text-muted-ink font-light mb-8">{{ total }} entrées dans le journal.</p>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!items.length" class="border border-rule p-12 text-center font-serif italic text-muted-ink">Aucune erreur. Tout va bien.</div>

		<ul v-else class="border-t border-rule">
			<li v-for="row in items" :key="row.id" class="border-b border-rule">
				<button class="w-full text-left py-4 px-2 grid grid-cols-12 gap-3 items-baseline hover:bg-paper" @click="toggle(row.id)">
					<span class="col-span-3 text-[10px] uppercase tracking-widest text-muted-ink">
						{{ new Date(row.createdAt).toLocaleString("fr-FR") }}
					</span>
					<span class="col-span-1 text-[10px] uppercase tracking-widest font-semibold" :class="row.level === 'ERROR' ? 'text-destructive' : 'text-muted-ink'">
						{{ row.level }}
					</span>
					<span class="col-span-8 font-serif text-base text-ink truncate">{{ row.message }}</span>
				</button>
				<pre v-if="opened === row.id" class="bg-ink text-paper text-xs p-4 overflow-auto mb-2 mx-2">{{ row.stack || JSON.stringify(row.context, null, 2) }}</pre>
			</li>
		</ul>

		<div class="flex items-center justify-between mt-6 text-[10px] uppercase tracking-widest text-muted-ink">
			<button class="hover:text-brand disabled:opacity-30" :disabled="skip === 0" @click="skip = Math.max(0, skip - take)">← Précédent</button>
			<span>{{ items.length ? `${skip + 1}–${skip + items.length}` : "0" }} sur {{ total }}</span>
			<button class="hover:text-brand disabled:opacity-30" :disabled="skip + take >= total" @click="skip += take">Suivant →</button>
		</div>
	</div>
</template>
