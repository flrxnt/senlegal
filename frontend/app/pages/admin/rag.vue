<script setup lang="ts">
import { ref, onMounted } from "vue";
import { toast } from "vue-sonner";
import { Trash2, Upload as UploadIcon, FileText } from "lucide-vue-next";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatBytes } from "~/utils/plan";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Sources RAG — Admin", robots: "noindex,nofollow" });

interface RagDoc {
	id: string;
	filename: string;
	contentType: string;
	sizeBytes: number;
	createdAt: string;
}

const items = ref<RagDoc[]>([]);
const loading = ref(true);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

async function refresh() {
	loading.value = true;
	try {
		items.value = await useApi()<RagDoc[]>("/admin/rag/sources");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

onMounted(refresh);

function pick() {
	fileInput.value?.click();
}

async function onChange(e: Event) {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file) return;
	uploading.value = true;
	try {
		const fd = new FormData();
		fd.append("file", file);
		await useApi()("/admin/rag/sources", { method: "POST", body: fd });
		toast.success("Source ajoutée. La réindexation peut prendre quelques minutes.");
		await refresh();
	} catch (err) {
		toast.error(apiErrorMessage(err, "Téléversement impossible."));
	} finally {
		uploading.value = false;
		if (fileInput.value) fileInput.value.value = "";
	}
}

async function remove(d: RagDoc) {
	if (!globalThis.confirm(`Supprimer « ${d.filename} » de la base RAG ?`)) return;
	try {
		await useApi()(`/admin/rag/sources/${d.id}`, { method: "DELETE" });
		toast.success("Source supprimée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	}
}
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Sources <span class="italic font-light text-brand">RAG</span>.</h1>
		<p class="text-muted-ink font-light mb-8 max-w-xl">PDF officiels indexés dans la base juridique (Code des marchés, jurisprudence ARCOP, doctrine).</p>

		<div class="flex items-center justify-between mb-8 border-t border-b border-rule py-4">
			<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold">{{ items.length }} source(s)</p>
			<button
				class="bg-brand text-paper px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
				:disabled="uploading"
				@click="pick"
			>
				<UploadIcon :size="14" />
				{{ uploading ? "Téléversement…" : "Ajouter un PDF" }}
			</button>
			<input ref="fileInput" type="file" accept="application/pdf" class="hidden" @change="onChange" />
		</div>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!items.length" class="border border-rule p-12 text-center font-serif italic text-muted-ink">Aucune source pour l'instant.</div>

		<ul v-else class="border-t border-rule">
			<li v-for="d in items" :key="d.id" class="border-b border-rule py-4 grid grid-cols-12 gap-4 items-center px-2 hover:bg-paper">
				<span class="col-span-12 md:col-span-7 font-serif text-base text-ink truncate flex items-center gap-3">
					<FileText :size="16" class="text-brand shrink-0" />
					{{ d.filename }}
				</span>
				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">{{ formatBytes(d.sizeBytes) }}</span>
				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
					{{ new Date(d.createdAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }) }}
				</span>
				<div class="col-span-12 md:col-span-1 flex justify-end">
					<button class="text-muted-ink hover:text-destructive p-2" :aria-label="`Supprimer ${d.filename}`" @click="remove(d)">
						<Trash2 :size="16" />
					</button>
				</div>
			</li>
		</ul>
	</div>
</template>
