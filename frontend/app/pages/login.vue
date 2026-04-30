<script setup lang="ts">
import { ref, computed } from "vue";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";

definePageMeta({ layout: "auth" });
useSeoMeta({
	title: "Accès — SenLégal",
	description: "Identifiez-vous pour consulter le Code des Marchés Publics avec SenLégal.",
	robots: "noindex,nofollow",
});

const route = useRoute();
const auth = useAuthStore();

const isLogin = ref(true);
const name = ref("");
const email = ref("");
const password = ref("");
const submitting = ref(false);
const errorMsg = ref<string | null>(null);

const heading = computed(() => (isLogin.value ? "Accès Restreint." : "Ouvrir un registre."));
const cta = computed(() => (isLogin.value ? "Entrer dans la salle" : "S'enregistrer"));

async function onSubmit() {
	errorMsg.value = null;
	submitting.value = true;
	try {
		if (isLogin.value) {
			await auth.login(email.value, password.value);
		} else {
			await auth.register({ name: name.value || undefined, email: email.value, password: password.value });
		}
		toast.success("Session ouverte.");
		const next = (route.query.next as string) || "/app";
		await navigateTo(next);
	} catch (e: unknown) {
		const err = e as { data?: { statusMessage?: string }; message?: string };
		errorMsg.value = err.data?.statusMessage || err.message || "Identifiants invalides.";
	} finally {
		submitting.value = false;
	}
}
</script>

<template>
	<div class="w-full max-w-md mt-12 md:mt-0">
		<div class="text-center mb-10 md:mb-12">
			<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand mb-6 md:mb-8 inline-block"> SenLégal. </NuxtLink>
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-3 md:mb-4">{{ heading }}</h1>
			<p class="text-muted-ink text-xs md:text-sm font-light px-4">Veuillez vous identifier pour consulter l'archive.</p>
		</div>

		<UiCard class="rounded-none shadow-sm">
			<form class="space-y-6" @submit.prevent="onSubmit">
				<div v-if="!isLogin">
					<UiLabel>Nom et Qualité</UiLabel>
					<UiInput v-model="name" type="text" required placeholder="Maître Fall…" autocomplete="name" />
				</div>
				<div>
					<UiLabel>Identifiant (Email)</UiLabel>
					<UiInput v-model="email" type="email" required placeholder="avocat@cabinet.sn" autocomplete="email" />
				</div>
				<div>
					<div class="flex justify-between items-center mb-2">
						<UiLabel class="mb-0">Code secret</UiLabel>
						<NuxtLink v-if="isLogin" to="/forgot-password" class="text-[10px] md:text-xs text-brand hover:text-brand-dark"> Oublié ? </NuxtLink>
					</div>
					<UiInput v-model="password" type="password" required placeholder="••••••••" :autocomplete="isLogin ? 'current-password' : 'new-password'" />
				</div>

				<p v-if="errorMsg" class="text-xs text-destructive font-sans uppercase tracking-widest" role="alert">
					{{ errorMsg }}
				</p>

				<UiButton type="submit" variant="primary" size="lg" class="w-full mt-6" :disabled="submitting">
					{{ submitting ? "…" : cta }}
				</UiButton>
			</form>

			<div
				class="mt-8 md:mt-10 text-center text-[10px] md:text-xs tracking-wide text-muted-ink uppercase border-t border-rule pt-6 md:pt-8 flex flex-col sm:flex-row items-center justify-center gap-2"
			>
				<span>{{ isLogin ? "Nouveau membre ?" : "Déjà enregistré ?" }}</span>
				<button type="button" class="text-brand font-semibold border-b border-brand pb-0.5 hover:text-brand-dark hover:border-brand-dark" @click="isLogin = !isLogin">
					{{ isLogin ? "Créer un dossier" : "S'identifier" }}
				</button>
			</div>
		</UiCard>
	</div>
</template>
