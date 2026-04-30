<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { toast } from "vue-sonner";
import { Trash2, Download, Upload as UploadIcon, FileText } from "lucide-vue-next";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatBytes } from "~/utils/plan";

definePageMeta({});
useSeoMeta({ title: "Coffre-fort — SenLégal", robots: "noindex,nofollow" });

interface UserDoc {
	id: string;
	kind: string;
	filename: string;
	contentType: string;
	sizeBytes: number;
	createdAt: string;
}
interface Usage {
	storageUsedBytes: number;
	storageQuotaBytes: number;
	maxUserDocumentMb: number;
}

const docs = ref<UserDoc[]>([]);
const usage = ref<Usage | null>(null);
const loading = ref(true);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const visibleDocs = computed(() => docs.value.filter((d) => d.kind === "USER_PRIVATE"));

async function refresh() {
	loading.value = true;
	try {
		const [list, u] = await Promise.all([useApi()<UserDoc[]>("/me/documents"), useApi()<Usage>("/me/usage")]);
		docs.value = list;
		usage.value = u;
	} catch (e) {
		toast.error(apiErrorMessage(e, "Impossible de charger vos documents."));
	} finally {
		loading.value = false;
	}
}

onMounted(refresh);

function pickFile() {
	fileInput.value?.click();
}

async function onFileChange(e: Event) {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file) return;
	uploading.value = true;
	try {
		const fd = new FormData();
		fd.append("file", file);
		await useApi()("/me/documents", { method: "POST", body: fd });
		toast.success("Document ajouté.");
		await refresh();
	} catch (err) {
		toast.error(apiErrorMessage(err, "Téléversement impossible."));
	} finally {
		uploading.value = false;
		if (fileInput.value) fileInput.value.value = "";
	}
}

async function download(id: string, name: string) {
	try {
		const res = await useApi()<{ url: string }>(`/documents/${id}/url`);
		const a = document.createElement("a");
		a.href = res.url;
		a.target = "_blank";
		a.rel = "noopener";
		a.download = name;
		document.body.appendChild(a);
		a.click();
		a.remove();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Lien indisponible."));
	}
}

async function remove(id: string, name: string) {
	if (!globalThis.confirm(`Supprimer « ${name} » ?`)) return;
	try {
		await useApi()(`/me/documents/${id}`, { method: "DELETE" });
		toast.success("Document supprimé.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	}
}

const usagePercent = computed(() => {
	if (!usage.value || !usage.value.storageQuotaBytes) return 0;
	return Math.min(100, Math.round((usage.value.storageUsedBytes / usage.value.storageQuotaBytes) * 100));
});
</script>

<template>
	<LayoutDashboardShell>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-4">Coffre-<span class="italic font-light text-brand">fort</span>.</h1>
		<p class="text-muted-ink font-light mb-12 max-w-xl">Importez vos pièces (DAO, mémoires, contrats) pour les conserver chiffrées et accessibles depuis vos consultations.</p>

		<div v-if="usage" class="border-t border-b border-rule py-6 mb-12">
			<div class="flex items-baseline justify-between mb-3">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold">Stockage utilisé</p>
				<p class="text-xs font-sans text-ink">
					<span class="font-serif text-lg">{{ formatBytes(usage.storageUsedBytes) }}</span>
					<span class="text-muted-ink"> / {{ formatBytes(usage.storageQuotaBytes) }}</span>
				</p>
			</div>
			<div class="h-1 bg-rule">
				<div class="h-full bg-brand transition-all" :style="{ width: `${usagePercent}%` }" />
			</div>
			<p class="text-[10px] text-muted-ink mt-3">Taille maximale par document : {{ usage.maxUserDocumentMb }} Mo.</p>
		</div>

		<div class="flex items-center justify-between mb-8">
			<h2 class="font-serif text-2xl text-ink">Documents</h2>
			<button
				class="bg-brand text-paper px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:bg-brand-dark transition-colors flex items-center gap-2"
				:disabled="uploading"
				@click="pickFile"
			>
				<UploadIcon :size="14" />
				{{ uploading ? "Téléversement…" : "Ajouter un document" }}
			</button>
			<input ref="fileInput" type="file" class="hidden" @change="onFileChange" />
		</div>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!visibleDocs.length" class="border border-rule p-12 text-center">
			<FileText :size="32" class="mx-auto text-muted-ink mb-4" />
			<p class="font-serif italic text-xl text-muted-ink">Aucun document pour l'instant.</p>
		</div>

		<ul v-else class="border-t border-rule">
			<li v-for="d in visibleDocs" :key="d.id" class="border-b border-rule py-5 px-2 grid grid-cols-12 gap-4 items-center hover:bg-paper transition-colors">
				<span class="col-span-12 md:col-span-6 font-serif text-base md:text-lg text-ink truncate flex items-center gap-3">
					<FileText :size="16" class="text-brand shrink-0" />
					{{ d.filename }}
				</span>
				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">{{ formatBytes(d.sizeBytes) }}</span>
				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
					{{ new Date(d.createdAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }) }}
				</span>
				<div class="col-span-12 md:col-span-2 flex items-center justify-end gap-2">
					<button class="text-muted-ink hover:text-brand p-2" :aria-label="`Télécharger ${d.filename}`" @click="download(d.id, d.filename)">
						<Download :size="16" />
					</button>
					<button class="text-muted-ink hover:text-destructive p-2" :aria-label="`Supprimer ${d.filename}`" @click="remove(d.id, d.filename)">
						<Trash2 :size="16" />
					</button>
				</div>
			</li>
		</ul>
	</LayoutDashboardShell>
</template>
