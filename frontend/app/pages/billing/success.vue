<script setup lang="ts">
import { onMounted, ref } from "vue";
import { toast } from "vue-sonner";
import { useApi, apiErrorMessage } from "~/composables/useApi";
import { useAuthStore } from "~/stores/auth";

definePageMeta({ layout: "auth" });
useSeoMeta({ title: "Paiement validé — SenLégal", robots: "noindex,nofollow" });

const route = useRoute();
const auth = useAuthStore();
const status = ref<"loading" | "ok" | "pending" | "failed">("loading");
const tries = ref(0);

async function check() {
	const invoiceId = route.query.invoice as string | undefined;
	if (!invoiceId) {
		status.value = "failed";
		return;
	}
	try {
		const res = await useApi()<{ status: string }>(`/payments/reconcile/${invoiceId}`, { method: "POST" });
		if (res.status === "PAID") {
			status.value = "ok";
			await auth.refreshMe();
			return;
		}
		if (tries.value < 5) {
			tries.value++;
			setTimeout(check, 3000);
			status.value = "pending";
		} else {
			status.value = "pending";
		}
	} catch (e) {
		status.value = "failed";
		toast.error(apiErrorMessage(e, "Vérification du paiement impossible."));
	}
}

onMounted(check);
</script>

<template>
	<div class="w-full max-w-lg text-center">
		<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand mb-8 inline-block">SenLégal.</NuxtLink>

		<template v-if="status === 'loading' || status === 'pending'">
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-4">Paiement <span class="italic text-brand">en cours</span>.</h1>
			<p class="text-sm text-muted-ink font-light mb-8">Nous vérifions la confirmation du prestataire. Patientez quelques secondes…</p>
			<div class="inline-flex gap-1 items-center text-muted-ink">
				<span class="w-2 h-2 bg-brand rounded-full animate-pulse" />
				<span class="w-2 h-2 bg-brand/70 rounded-full animate-pulse [animation-delay:120ms]" />
				<span class="w-2 h-2 bg-brand/40 rounded-full animate-pulse [animation-delay:240ms]" />
			</div>
		</template>

		<template v-else-if="status === 'ok'">
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-4">Bienvenue au <span class="italic text-brand">Cabinet</span>.</h1>
			<p class="text-sm text-muted-ink font-light mb-10">Votre abonnement est actif. Bonnes consultations.</p>
			<UiButton to="/app" variant="primary" size="lg">Reprendre la consultation</UiButton>
		</template>

		<template v-else>
			<h1 class="font-serif text-3xl md:text-4xl text-ink mb-4">Vérification <span class="italic text-destructive">impossible</span>.</h1>
			<p class="text-sm text-muted-ink font-light mb-10">Nous n'avons pas pu confirmer votre paiement. Réessayez ou contactez le support.</p>
			<UiButton to="/dashboard/facturation" variant="outline" size="lg">Retour à la facturation</UiButton>
		</template>
	</div>
</template>
