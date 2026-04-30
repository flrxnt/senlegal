<script setup lang="ts">
import { ref } from "vue";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";
import { apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "auth" });
useSeoMeta({ title: "Mot de passe oublié — SenLégal", robots: "noindex,nofollow" });

const auth = useAuthStore();
const email = ref("");
const submitting = ref(false);
const sent = ref(false);

async function submit() {
	submitting.value = true;
	try {
		await auth.forgotPassword(email.value);
		sent.value = true;
		toast.success("Si un compte existe, un lien vous a été envoyé.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Envoi impossible."));
	} finally {
		submitting.value = false;
	}
}
</script>

<template>
	<div class="w-full max-w-md mt-12 md:mt-0">
		<div class="text-center mb-10 md:mb-12">
			<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand mb-6 md:mb-8 inline-block">SenLégal.</NuxtLink>
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-3 md:mb-4">Mot de passe <span class="italic text-brand">oublié</span>.</h1>
			<p class="text-muted-ink text-xs md:text-sm font-light px-4">Indiquez votre email, nous vous enverrons un lien de réinitialisation.</p>
		</div>

		<UiCard class="rounded-none shadow-sm">
			<div v-if="sent" class="text-center py-6">
				<p class="font-serif text-2xl text-ink mb-3">Vérifiez votre boîte mail.</p>
				<p class="text-sm text-muted-ink font-light mb-6">
					Si un compte existe pour <span class="text-ink">{{ email }}</span
					>, un lien sécurisé vient de partir.
				</p>
				<NuxtLink to="/login" class="text-[10px] uppercase tracking-widest font-semibold text-brand border-b border-brand pb-1">← Retour à la connexion</NuxtLink>
			</div>
			<form v-else class="space-y-6" @submit.prevent="submit">
				<div>
					<UiLabel>Email</UiLabel>
					<UiInput v-model="email" type="email" required autocomplete="email" placeholder="avocat@cabinet.sn" />
				</div>
				<UiButton type="submit" variant="primary" size="lg" class="w-full" :disabled="submitting">
					{{ submitting ? "…" : "Envoyer le lien" }}
				</UiButton>
				<NuxtLink to="/login" class="block text-center text-[10px] uppercase tracking-widest text-muted-ink hover:text-brand pt-4 border-t border-rule">
					← Retour à la connexion
				</NuxtLink>
			</form>
		</UiCard>
	</div>
</template>
