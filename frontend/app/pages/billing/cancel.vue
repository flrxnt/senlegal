<script setup lang="ts">
definePageMeta({ layout: "auth" });
useSeoMeta({ title: "Paiement annulé — SenLégal", robots: "noindex,nofollow" });
</script>

<template>
	<div class="w-full max-w-lg text-center">
		<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand mb-8 inline-block">SenLégal.</NuxtLink>
		<h1 class="font-serif text-3xl md:text-4xl text-ink mb-4">Paiement <span class="italic text-muted-ink">annulé</span>.</h1>
		<p class="text-sm text-muted-ink font-light mb-10">Aucun montant n'a été débité. Vous pouvez relancer la souscription quand vous le souhaitez.</p>
		<UiButton to="/dashboard/facturation" variant="primary" size="lg">Retour à la facturation</UiButton>
	</div>
</template>
