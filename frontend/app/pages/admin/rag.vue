<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { toast } from "vue-sonner";
import { Trash2, Upload as UploadIcon, FileText, RotateCw, Loader2, CheckCircle2, AlertCircle, Clock } from "lucide-vue-next";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { useAuthToken } from "~/composables/useAuthToken";
import { formatBytes } from "~/utils/plan";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Sources RAG — Admin", robots: "noindex,nofollow" });

type IngestStatus = "PENDING" | "PROCESSING" | "READY" | "FAILED";

interface RagDoc {
	id: string;
	filename: string;
	contentType: string;
	sizeBytes: number;
	createdAt: string;
	ingestStatus: IngestStatus;
	ingestError: string | null;
	ingestedAt: string | null;
	ingestStartedAt: string | null;
	metadata: Record<string, unknown> | null;
}

const items = ref<RagDoc[]>([]);
const loading = ref(true);
const uploading = ref(false);
const uploadProgress = ref(0); // 0-100, progression du téléversement uniquement
const fileInput = ref<HTMLInputElement | null>(null);
const reingestingIds = ref(new Set<string>());

const config = useRuntimeConfig();
const token = useAuthToken();

const hasPending = computed(() => items.value.some((d) => d.ingestStatus === "PENDING" || d.ingestStatus === "PROCESSING"));

const stats = computed(() => {
	const total = items.value.length;
	const ready = items.value.filter((d) => d.ingestStatus === "READY").length;
	const processing = items.value.filter((d) => d.ingestStatus === "PROCESSING" || d.ingestStatus === "PENDING").length;
	const failed = items.value.filter((d) => d.ingestStatus === "FAILED").length;
	return { total, ready, processing, failed };
});

let pollHandle: ReturnType<typeof setInterval> | null = null;

async function refresh() {
	try {
		items.value = await useApi()<RagDoc[]>("/admin/rag/sources");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

function startPolling() {
	if (pollHandle) return;
	pollHandle = setInterval(() => {
		if (hasPending.value) refresh();
	}, 3000);
}

function stopPolling() {
	if (pollHandle) {
		clearInterval(pollHandle);
		pollHandle = null;
	}
}

onMounted(async () => {
	await refresh();
	startPolling();
});

onUnmounted(stopPolling);

function pick() {
	fileInput.value?.click();
}

function uploadWithProgress(file: File): Promise<RagDoc> {
	const baseURL = (config.public.apiBase as string) || "/api";
	return new Promise<RagDoc>((resolve, reject) => {
		const xhr = new XMLHttpRequest();
		xhr.open("POST", `${baseURL.replace(/\/$/, "")}/admin/rag/sources`);
		if (token.value) xhr.setRequestHeader("Authorization", `Bearer ${token.value}`);
		xhr.upload.onprogress = (e) => {
			if (e.lengthComputable) uploadProgress.value = Math.round((e.loaded / e.total) * 100);
		};
		xhr.onload = () => {
			if (xhr.status >= 200 && xhr.status < 300) {
				try {
					resolve(JSON.parse(xhr.responseText) as RagDoc);
				} catch (err) {
					reject(err as Error);
				}
			} else {
				let msg = `HTTP ${xhr.status}`;
				try {
					const body = JSON.parse(xhr.responseText);
					msg = body?.message || body?.error || msg;
				} catch {
					/* ignore parse error */
				}
				reject(new Error(msg));
			}
		};
		xhr.onerror = () => reject(new Error("Erreur réseau."));
		xhr.onabort = () => reject(new Error("Téléversement annulé."));
		const fd = new FormData();
		fd.append("file", file);
		xhr.send(fd);
	});
}

async function onChange(e: Event) {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file) return;
	if (!/\.pdf$/i.test(file.name) && file.type !== "application/pdf") {
		toast.error("Seuls les PDFs sont acceptés.");
		if (fileInput.value) fileInput.value.value = "";
		return;
	}
	uploading.value = true;
	uploadProgress.value = 0;
	try {
		await uploadWithProgress(file);
		toast.success("PDF téléversé. L'indexation démarre…");
		await refresh();
	} catch (err) {
		toast.error(apiErrorMessage(err, "Téléversement impossible."));
	} finally {
		uploading.value = false;
		uploadProgress.value = 0;
		if (fileInput.value) fileInput.value.value = "";
	}
}

async function reingest(d: RagDoc) {
	if (reingestingIds.value.has(d.id)) return;
	reingestingIds.value.add(d.id);
	try {
		await useApi()(`/admin/rag/sources/${d.id}/reingest`, { method: "POST" });
		toast.success("Réindexation lancée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Réindexation impossible."));
	} finally {
		reingestingIds.value.delete(d.id);
	}
}

async function remove(d: RagDoc) {
	if (!globalThis.confirm(`Supprimer « ${d.filename} » de la base RAG ? Cette action est irréversible.`)) return;
	try {
		await useApi()(`/admin/rag/sources/${d.id}`, { method: "DELETE" });
		toast.success("Source supprimée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	}
}

function statusLabel(s: IngestStatus): string {
	switch (s) {
		case "PENDING":
			return "En attente";
		case "PROCESSING":
			return "Indexation…";
		case "READY":
			return "Indexé";
		case "FAILED":
			return "Échec";
	}
}

function chunkCount(d: RagDoc): number | null {
	const m = d.metadata as { chunks?: number } | null;
	return m && typeof m.chunks === "number" ? m.chunks : null;
}
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Sources <span class="italic font-light text-brand">RAG</span>.</h1>
		<p class="text-muted-ink font-light mb-8 max-w-xl">
			PDF officiels indexés dans la base juridique (Code des marchés, jurisprudence ARCOP, doctrine). Stockés dans MinIO ; ré-indexables sans ré-upload.
		</p>

		<div class="flex items-center justify-between mb-4 border-t border-b border-rule py-4 gap-4 flex-wrap">
			<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold">
				{{ stats.total }} source(s)
				<span v-if="stats.ready" class="text-brand ml-2">· {{ stats.ready }} prête(s)</span>
				<span v-if="stats.processing" class="text-amber-700 ml-2">· {{ stats.processing }} en cours</span>
				<span v-if="stats.failed" class="text-destructive ml-2">· {{ stats.failed }} en échec</span>
			</p>
			<button
				class="bg-brand text-paper px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50"
				:disabled="uploading"
				@click="pick"
			>
				<UploadIcon :size="14" />
				{{ uploading ? `Téléversement… ${uploadProgress}%` : "Ajouter un PDF" }}
			</button>
			<input ref="fileInput" type="file" accept="application/pdf,.pdf" class="hidden" @change="onChange" />
		</div>

		<div v-if="uploading" class="mb-6 h-1 bg-rule overflow-hidden">
			<div class="h-full bg-brand transition-all duration-150" :style="{ width: `${uploadProgress}%` }" />
		</div>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!items.length" class="border border-rule p-12 text-center font-serif italic text-muted-ink">Aucune source pour l'instant.</div>

		<ul v-else class="border-t border-rule">
			<li v-for="d in items" :key="d.id" class="border-b border-rule py-4 grid grid-cols-12 gap-3 items-center px-2 hover:bg-paper">
				<span class="col-span-12 md:col-span-5 font-serif text-base text-ink truncate flex items-center gap-3">
					<FileText :size="16" class="text-brand shrink-0" />
					<span class="truncate" :title="d.filename">{{ d.filename }}</span>
				</span>

				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest font-semibold flex items-center gap-2">
					<Loader2 v-if="d.ingestStatus === 'PROCESSING'" :size="14" class="text-amber-700 animate-spin" />
					<Clock v-else-if="d.ingestStatus === 'PENDING'" :size="14" class="text-muted-ink" />
					<CheckCircle2 v-else-if="d.ingestStatus === 'READY'" :size="14" class="text-brand" />
					<AlertCircle v-else :size="14" class="text-destructive" />
					<span
						:class="{
							'text-amber-700': d.ingestStatus === 'PROCESSING',
							'text-muted-ink': d.ingestStatus === 'PENDING',
							'text-brand': d.ingestStatus === 'READY',
							'text-destructive': d.ingestStatus === 'FAILED',
						}"
						>{{ statusLabel(d.ingestStatus) }}</span
					>
				</span>

				<span class="col-span-3 md:col-span-1 text-[10px] uppercase tracking-widest text-muted-ink">{{ formatBytes(d.sizeBytes) }}</span>

				<span class="col-span-3 md:col-span-1 text-[10px] uppercase tracking-widest text-muted-ink">
					<template v-if="chunkCount(d) !== null">{{ chunkCount(d) }} chunks</template>
				</span>

				<span class="col-span-6 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
					{{ new Date(d.createdAt).toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" }) }}
				</span>

				<div class="col-span-12 md:col-span-1 flex justify-end gap-1">
					<button
						v-if="d.ingestStatus === 'FAILED' || d.ingestStatus === 'READY'"
						class="text-muted-ink hover:text-brand p-2 disabled:opacity-30"
						:disabled="reingestingIds.has(d.id)"
						:aria-label="`Réindexer ${d.filename}`"
						title="Réindexer"
						@click="reingest(d)"
					>
						<RotateCw :size="16" :class="{ 'animate-spin': reingestingIds.has(d.id) }" />
					</button>
					<button
						class="text-muted-ink hover:text-destructive p-2 disabled:opacity-30"
						:disabled="d.ingestStatus === 'PROCESSING'"
						:aria-label="`Supprimer ${d.filename}`"
						title="Supprimer"
						@click="remove(d)"
					>
						<Trash2 :size="16" />
					</button>
				</div>

				<p v-if="d.ingestError && d.ingestStatus === 'FAILED'" class="col-span-12 text-xs text-destructive bg-destructive/5 px-3 py-2 border border-destructive/20">
					{{ d.ingestError }}
				</p>
			</li>
		</ul>
	</div>
</template>
