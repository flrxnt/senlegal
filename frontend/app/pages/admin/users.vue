<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "admin" });
useSeoMeta({ title: "Utilisateurs — Admin", robots: "noindex,nofollow" });

interface AdminUser {
	id: string;
	email: string;
	name: string | null;
	role: "USER" | "ADMIN";
	plan: "FREE" | "PRO";
	isActive: boolean;
	createdAt: string;
	lastLoginAt: string | null;
}

const items = ref<AdminUser[]>([]);
const total = ref(0);
const loading = ref(false);
const skip = ref(0);
const take = ref(25);
const q = ref("");
const planFilter = ref<"" | "FREE" | "PRO">("");
const roleFilter = ref<"" | "USER" | "ADMIN">("");

async function load() {
	loading.value = true;
	try {
		const params = new URLSearchParams();
		params.set("skip", String(skip.value));
		params.set("take", String(take.value));
		if (q.value) params.set("q", q.value);
		if (planFilter.value) params.set("plan", planFilter.value);
		if (roleFilter.value) params.set("role", roleFilter.value);
		const res = await useApi()<{ items: AdminUser[]; total: number }>(`/admin/users?${params}`);
		items.value = res.items;
		total.value = res.total;
	} catch (e) {
		toast.error(apiErrorMessage(e, "Chargement impossible."));
	} finally {
		loading.value = false;
	}
}

let debounce: ReturnType<typeof setTimeout> | null = null;
watch([q, planFilter, roleFilter], () => {
	if (debounce) clearTimeout(debounce);
	debounce = setTimeout(() => {
		skip.value = 0;
		load();
	}, 250);
});
watch(skip, load);

onMounted(load);

async function patch(u: AdminUser, data: Partial<Pick<AdminUser, "role" | "plan" | "isActive">>) {
	try {
		const updated = await useApi()<AdminUser>(`/admin/users/${u.id}`, { method: "PATCH", body: data });
		Object.assign(u, updated);
		toast.success("Utilisateur mis à jour.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Modification impossible."));
	}
}

async function remove(u: AdminUser) {
	if (!globalThis.confirm(`Supprimer ${u.email} ?`)) return;
	try {
		await useApi()(`/admin/users/${u.id}`, { method: "DELETE" });
		toast.success("Utilisateur supprimé.");
		await load();
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	}
}

const columns = [
	{ key: "email", label: "Email", span: 4 },
	{ key: "role", label: "Rôle", span: 2 },
	{ key: "plan", label: "Plan", span: 2 },
	{ key: "isActive", label: "Statut", span: 2 },
	{ key: "actions", label: "", span: 2 },
];
</script>

<template>
	<div>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-3">Utilisateurs.</h1>
		<p class="text-muted-ink font-light mb-8">{{ total }} comptes enregistrés.</p>

		<div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
			<UiInput v-model="q" placeholder="Rechercher par email ou nom" />
			<select v-model="planFilter" class="border border-rule bg-paper px-4 py-2 font-sans text-sm">
				<option value="">Tous les plans</option>
				<option value="FREE">FREE</option>
				<option value="PRO">PRO</option>
			</select>
			<select v-model="roleFilter" class="border border-rule bg-paper px-4 py-2 font-sans text-sm">
				<option value="">Tous les rôles</option>
				<option value="USER">USER</option>
				<option value="ADMIN">ADMIN</option>
			</select>
		</div>

		<AdminDataTable :columns="columns" :rows="items" :loading="loading" :total="total" :skip="skip" :take="take" empty-label="Aucun utilisateur." @update:skip="(v) => (skip = v)">
			<template #email="{ row }">
				<div class="truncate">
					<p class="font-serif text-base text-ink truncate">{{ row.email }}</p>
					<p class="text-[10px] text-muted-ink truncate">{{ row.name || "—" }}</p>
				</div>
			</template>
			<template #role="{ row }">
				<select
					:value="row.role"
					class="bg-paper border border-rule text-xs px-2 py-1"
					@change="patch(row, { role: ($event.target as HTMLSelectElement).value as 'USER' | 'ADMIN' })"
				>
					<option value="USER">USER</option>
					<option value="ADMIN">ADMIN</option>
				</select>
			</template>
			<template #plan="{ row }">
				<select
					:value="row.plan"
					class="bg-paper border border-rule text-xs px-2 py-1"
					@change="patch(row, { plan: ($event.target as HTMLSelectElement).value as 'FREE' | 'PRO' })"
				>
					<option value="FREE">FREE</option>
					<option value="PRO">PRO</option>
				</select>
			</template>
			<template #isActive="{ row }">
				<button
					class="text-[10px] uppercase tracking-widest font-semibold px-2 py-1 border"
					:class="row.isActive ? 'border-brand text-brand' : 'border-destructive text-destructive'"
					@click.stop="patch(row, { isActive: !row.isActive })"
				>
					{{ row.isActive ? "Actif" : "Désactivé" }}
				</button>
			</template>
			<template #actions="{ row }">
				<button class="text-[10px] uppercase tracking-widest font-semibold text-destructive hover:opacity-70" @click.stop="remove(row)">Supprimer</button>
			</template>
		</AdminDataTable>
	</div>
</template>
