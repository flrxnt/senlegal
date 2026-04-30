<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { toast } from "vue-sonner";
import { Archive, Database, Download, HardDrive, Trash2, Upload as UploadIcon } from "lucide-vue-next";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { formatBytes } from "~/utils/plan";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Sauvegardes — Admin", robots: "noindex,nofollow" });

interface BackupItem {
	key: string;
	size: number;
	lastModified: string | null;
}

const items = ref<BackupItem[]>([]);
const loading = ref(true);
const creatingFull = ref(false);
const creatingDb = ref(false);
const restoring = ref(false);
const downloading = ref<string | null>(null);
const deleting = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

async function refresh() {
	loading.value = true;
	try {
		items.value = await useApi()<BackupItem[]>("/admin/backups");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

onMounted(refresh);

async function createFull() {
	if (creatingFull.value) return;
	creatingFull.value = true;
	toast.info("Sauvegarde complète en cours… cela peut prendre un instant.");
	try {
		await useApi()("/admin/backups/full", { method: "POST" });
		toast.success("Sauvegarde complète créée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "La sauvegarde a échoué."));
	} finally {
		creatingFull.value = false;
	}
}

async function createDb() {
	if (creatingDb.value) return;
	creatingDb.value = true;
	try {
		await useApi()("/admin/backups/database", { method: "POST" });
		toast.success("Sauvegarde base de données créée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "La sauvegarde a échoué."));
	} finally {
		creatingDb.value = false;
	}
}

async function download(item: BackupItem) {
	if (downloading.value) return;
	downloading.value = item.key;
	try {
		const { url } = await useApi()<{ url: string; expiresIn: number }>("/admin/backups/download-url", { params: { key: item.key } });
		// Ouvre le lien signé MinIO/S3 dans un onglet pour déclencher le download.
		globalThis.open(url, "_blank", "noopener");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Téléchargement impossible."));
	} finally {
		downloading.value = null;
	}
}

async function remove(item: BackupItem) {
	if (!globalThis.confirm(`Supprimer définitivement la sauvegarde « ${shortName(item.key)} » ?`)) return;
	deleting.value = item.key;
	try {
		await useApi()("/admin/backups", { method: "DELETE", params: { key: item.key } });
		toast.success("Sauvegarde supprimée.");
		await refresh();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	} finally {
		deleting.value = null;
	}
}

function pickRestore() {
	fileInput.value?.click();
}

async function onRestoreFile(e: Event) {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file) return;
	const lower = file.name.toLowerCase();
	if (!lower.endsWith(".zip") && !lower.endsWith(".json")) {
		toast.error("Format non supporté (.zip ou .json attendu).");
		if (fileInput.value) fileInput.value.value = "";
		return;
	}
	const ok = globalThis.confirm(
		`Restaurer depuis « ${file.name} » ?\n\nCette opération va RÉINJECTER les données contenues dans l'archive (sans écraser les enregistrements déjà présents). À utiliser sur un environnement contrôlé.`,
	);
	if (!ok) {
		if (fileInput.value) fileInput.value.value = "";
		return;
	}
	restoring.value = true;
	try {
		const fd = new FormData();
		fd.append("file", file);
		const res = await useApi()<{ restored: Record<string, number>; storageRestored?: number }>("/admin/backups/restore", { method: "POST", body: fd });
		const totalRows = Object.values(res.restored ?? {}).reduce((a, b) => a + b, 0);
		const storageMsg = res.storageRestored == null ? "" : ` · ${res.storageRestored} fichier(s)`;
		toast.success(`Restauration terminée : ${totalRows} ligne(s)${storageMsg}.`);
		await refresh();
	} catch (err) {
		toast.error(apiErrorMessage(err, "Restauration impossible."));
	} finally {
		restoring.value = false;
		if (fileInput.value) fileInput.value.value = "";
	}
}

function shortName(key: string): string {
	const name = key.split("/").pop() ?? key;
	return name;
}

function isFull(key: string): boolean {
	return key.endsWith(".zip");
}

function formatDate(iso: string | null): string {
	if (!iso) return "—";
	try {
		return new Intl.DateTimeFormat("fr-FR", {
			dateStyle: "medium",
			timeStyle: "short",
		}).format(new Date(iso));
	} catch {
		return iso;
	}
}

const totals = computed(() => {
	const full = items.value.filter((i) => isFull(i.key)).length;
	const db = items.value.length - full;
	const size = items.value.reduce((acc, i) => acc + (i.size || 0), 0);
	return { full, db, size };
});
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Sauve<span class="italic font-light text-brand">gardes</span>.</h1>
		<p class="text-muted-ink font-light mb-12 max-w-xl">
			Archives complètes (base de données + objets MinIO) téléchargeables et restaurables. Conservez une copie hors-ligne avant toute opération critique.
		</p>

		<!-- Récap -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-px bg-rule border border-rule mb-10">
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Sauvegardes complètes</p>
				<p class="font-serif text-3xl text-ink">{{ totals.full }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Sauvegardes BDD</p>
				<p class="font-serif text-3xl text-ink">{{ totals.db }}</p>
			</div>
			<div class="bg-paper p-6">
				<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold mb-3">Volume total</p>
				<p class="font-serif text-3xl text-brand">{{ formatBytes(totals.size) }}</p>
			</div>
		</div>

		<!-- Actions -->
		<div class="border-t border-b border-rule py-6 mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
			<p class="text-[10px] uppercase tracking-widest text-muted-ink font-semibold">{{ items.length }} sauvegarde(s) sur le bucket</p>
			<div class="flex flex-wrap gap-3">
				<button
					class="border border-rule bg-paper text-ink px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:border-brand hover:text-brand transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
					:disabled="creatingDb || creatingFull"
					@click="createDb"
				>
					<Database :size="14" />
					{{ creatingDb ? "Export en cours…" : "Sauvegarde BDD" }}
				</button>
				<button
					class="bg-brand text-paper px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:bg-brand-dark transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
					:disabled="creatingFull || creatingDb"
					@click="createFull"
				>
					<Archive :size="14" />
					{{ creatingFull ? "Sauvegarde en cours…" : "Sauvegarde complète" }}
				</button>
				<button
					class="border border-destructive/40 text-destructive px-5 py-3 text-[10px] uppercase tracking-widest font-semibold hover:bg-destructive hover:text-paper transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
					:disabled="restoring"
					@click="pickRestore"
				>
					<UploadIcon :size="14" />
					{{ restoring ? "Restauration…" : "Restaurer une archive" }}
				</button>
				<input ref="fileInput" type="file" accept=".zip,.json,application/zip,application/json" class="hidden" @change="onRestoreFile" />
			</div>
		</div>

		<!-- Liste -->
		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink">Chargement…</p>

		<div v-else-if="!items.length" class="border border-rule p-12 text-center font-serif italic text-muted-ink">
			Aucune sauvegarde pour l'instant. Lancez une « Sauvegarde complète » pour archiver la base de données et les fichiers du bucket.
		</div>

		<ul v-else class="border-t border-rule">
			<li v-for="item in items" :key="item.key" class="border-b border-rule py-4 grid grid-cols-12 gap-3 md:gap-4 items-center px-2 hover:bg-paper transition-colors">
				<span class="col-span-12 md:col-span-6 font-serif text-base text-ink truncate flex items-center gap-3 min-w-0">
					<component :is="isFull(item.key) ? Archive : Database" :size="16" class="text-brand shrink-0" />
					<span class="truncate">{{ shortName(item.key) }}</span>
				</span>
				<span class="col-span-4 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
					<span class="inline-flex items-center gap-1.5 border border-rule px-2 py-1 font-semibold" :class="isFull(item.key) ? 'text-brand border-brand/40' : 'text-ink'">
						<HardDrive :size="11" />
						{{ isFull(item.key) ? "Complète" : "BDD" }}
					</span>
				</span>
				<span class="col-span-4 md:col-span-1 text-[10px] uppercase tracking-widest text-muted-ink">
					{{ formatBytes(item.size) }}
				</span>
				<span class="col-span-4 md:col-span-2 text-[10px] uppercase tracking-widest text-muted-ink">
					{{ formatDate(item.lastModified) }}
				</span>
				<span class="col-span-12 md:col-span-1 flex items-center justify-end gap-2">
					<button
						class="text-muted-ink hover:text-brand transition-colors disabled:opacity-50"
						:title="`Télécharger ${shortName(item.key)}`"
						:disabled="downloading === item.key"
						@click="download(item)"
					>
						<Download :size="16" />
					</button>
					<button
						class="text-muted-ink hover:text-destructive transition-colors disabled:opacity-50"
						:title="`Supprimer ${shortName(item.key)}`"
						:disabled="deleting === item.key"
						@click="remove(item)"
					>
						<Trash2 :size="16" />
					</button>
				</span>
			</li>
		</ul>

		<p class="mt-10 text-[10px] uppercase tracking-widest text-muted-ink">
			Format complet : <span class="text-ink">.zip</span> contenant <span class="text-ink">database.json</span> + <span class="text-ink">storage/</span>. Format BDD :
			<span class="text-ink">.json</span>.
		</p>
	</div>
</template>
