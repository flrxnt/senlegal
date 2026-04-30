<script setup lang="ts">
import { ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";
import { useApi, apiErrorMessage } from "~/composables/useApi";

definePageMeta({});
useSeoMeta({ title: "Compte — SenLégal", robots: "noindex,nofollow" });

const auth = useAuthStore();
const { user } = storeToRefs(auth);

const name = ref(user.value?.name || "");
const phone = ref(user.value?.phone || "");
const savingProfile = ref(false);

const currentPassword = ref("");
const newPassword = ref("");
const savingPassword = ref(false);

const avatarFile = ref<File | null>(null);
const uploadingAvatar = ref(false);
const avatarInput = ref<HTMLInputElement | null>(null);

watch(user, (u) => {
	if (!u) return;
	name.value = u.name || "";
	phone.value = u.phone || "";
});

async function saveProfile() {
	savingProfile.value = true;
	try {
		const updated = await useApi()<typeof user.value>("/me", {
			method: "PATCH",
			body: { name: name.value || undefined, phone: phone.value || undefined },
		});
		if (updated) auth.setUser(updated);
		toast.success("Profil mis à jour.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Mise à jour impossible."));
	} finally {
		savingProfile.value = false;
	}
}

async function changePassword() {
	if (newPassword.value.length < 8) {
		toast.error("Le nouveau mot de passe doit faire au moins 8 caractères.");
		return;
	}
	savingPassword.value = true;
	try {
		await useApi()("/me/password", {
			method: "POST",
			body: { currentPassword: currentPassword.value, newPassword: newPassword.value },
		});
		currentPassword.value = "";
		newPassword.value = "";
		toast.success("Mot de passe modifié.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Mot de passe incorrect."));
	} finally {
		savingPassword.value = false;
	}
}

function pickAvatar() {
	avatarInput.value?.click();
}

async function onAvatarChange(e: Event) {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file) return;
	avatarFile.value = file;
	uploadingAvatar.value = true;
	try {
		const fd = new FormData();
		fd.append("file", file);
		const updated = await useApi()<typeof user.value>("/me/avatar", { method: "POST", body: fd });
		if (updated) auth.setUser(updated);
		toast.success("Photo mise à jour.");
	} catch (err) {
		toast.error(apiErrorMessage(err, "Téléversement impossible."));
	} finally {
		uploadingAvatar.value = false;
		avatarFile.value = null;
		if (avatarInput.value) avatarInput.value.value = "";
	}
}
</script>

<template>
	<LayoutDashboardShell>
		<h1 class="font-serif text-4xl md:text-5xl text-ink mb-4">Mon <span class="italic font-light text-brand">compte</span>.</h1>
		<p class="text-muted-ink font-light mb-12 max-w-xl">Vos informations personnelles. Elles ne sont visibles que de vous.</p>

		<UiCard class="max-w-xl mb-8">
			<div class="flex items-center gap-6 mb-8">
				<div class="w-20 h-20 bg-paper border border-rule overflow-hidden flex items-center justify-center text-muted-ink font-serif text-2xl">
					<img v-if="user?.avatarUrl" :src="user.avatarUrl" :alt="user.name || user.email" class="w-full h-full object-cover" />
					<span v-else>{{ (user?.name || user?.email || "?").charAt(0).toUpperCase() }}</span>
				</div>
				<div>
					<button class="text-[10px] uppercase tracking-widest font-semibold text-brand border-b border-brand pb-1" :disabled="uploadingAvatar" @click="pickAvatar">
						{{ uploadingAvatar ? "Téléversement…" : "Modifier la photo" }}
					</button>
					<p class="text-[10px] text-muted-ink mt-2">PNG, JPG — max 2 Mo.</p>
					<input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="onAvatarChange" />
				</div>
			</div>

			<form class="space-y-6" @submit.prevent="saveProfile">
				<div>
					<UiLabel>Nom et qualité</UiLabel>
					<UiInput v-model="name" type="text" placeholder="Maître Fall" />
				</div>
				<div>
					<UiLabel>Email</UiLabel>
					<UiInput :model-value="user?.email" type="email" disabled />
				</div>
				<div>
					<UiLabel>Téléphone</UiLabel>
					<UiInput v-model="phone" type="tel" placeholder="+221 …" />
				</div>
				<UiButton type="submit" variant="primary" size="lg" class="w-full" :disabled="savingProfile">
					{{ savingProfile ? "Enregistrement…" : "Enregistrer" }}
				</UiButton>
			</form>
		</UiCard>

		<UiCard class="max-w-xl mb-8">
			<h2 class="font-serif text-2xl text-ink mb-6">Mot de passe</h2>
			<form class="space-y-6" @submit.prevent="changePassword">
				<div>
					<UiLabel>Mot de passe actuel</UiLabel>
					<UiInput v-model="currentPassword" type="password" autocomplete="current-password" required />
				</div>
				<div>
					<UiLabel>Nouveau mot de passe</UiLabel>
					<UiInput v-model="newPassword" type="password" autocomplete="new-password" required minlength="8" />
				</div>
				<UiButton type="submit" variant="outline" size="lg" class="w-full" :disabled="savingPassword">
					{{ savingPassword ? "…" : "Mettre à jour" }}
				</UiButton>
			</form>
		</UiCard>

		<div class="mt-16 border-t border-rule pt-12">
			<h2 class="font-serif text-2xl text-ink mb-3">Zone sensible</h2>
			<p class="text-sm text-muted-ink font-light mb-6">La suppression du compte entraîne l'effacement définitif de vos consultations et de vos documents.</p>
			<button
				class="text-[10px] uppercase tracking-widest font-semibold text-destructive border-b border-destructive pb-1 hover:opacity-80"
				@click="toast.error('Action non disponible — contactez le support.')"
			>
				Supprimer mon compte
			</button>
		</div>
	</LayoutDashboardShell>
</template>
