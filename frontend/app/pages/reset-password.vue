<script setup lang="ts">
import { ref, computed } from "vue";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";
import { apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "auth" });
useSeoMeta({ title: "Réinitialiser — SenLégal", robots: "noindex,nofollow" });

const route = useRoute();
const auth = useAuthStore();
const password = ref("");
const submitting = ref(false);
const done = ref(false);

const token = computed(() => (route.query.token as string) || "");

async function submit() {
	if (!token.value) {
		toast.error("Lien invalide.");
		return;
	}
	if (password.value.length < 8) {
		toast.error("8 caractères minimum.");
		return;
	}
	submitting.value = true;
	try {
		await auth.resetPassword(token.value, password.value);
		done.value = true;
		toast.success("Mot de passe réinitialisé.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Lien expiré ou invalide."));
	} finally {
		submitting.value = false;
	}
}
</script>

<template>
	<div class="w-full max-w-md mt-12 md:mt-0">
		<div class="text-center mb-10 md:mb-12">
			<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand mb-6 md:mb-8 inline-block">SenLégal.</NuxtLink>
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-3 md:mb-4">Nouveau <span class="italic text-brand">code secret</span>.</h1>
		</div>

		<UiCard class="rounded-none shadow-sm">
			<div v-if="done" class="text-center py-6">
				<p class="font-serif text-2xl text-ink mb-6">Mot de passe mis à jour.</p>
				<UiButton to="/login" variant="primary" size="lg">Se connecter</UiButton>
			</div>
			<form v-else class="space-y-6" @submit.prevent="submit">
				<div>
					<UiLabel>Nouveau mot de passe</UiLabel>
					<UiInput v-model="password" type="password" required autocomplete="new-password" minlength="8" />
				</div>
				<UiButton type="submit" variant="primary" size="lg" class="w-full" :disabled="submitting">
					{{ submitting ? "…" : "Définir le mot de passe" }}
				</UiButton>
			</form>
		</UiCard>
	</div>
</template>
