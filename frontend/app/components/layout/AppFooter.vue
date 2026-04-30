<script setup lang="ts">
const year = new Date().getFullYear();
</script>

<template>
	<footer class="py-12 px-6 md:px-12 bg-paper border-t border-rule flex flex-col md:flex-row justify-between items-center md:items-start gap-8">
		<NuxtLink to="/" class="font-serif italic text-2xl text-brand">SenLégal.</NuxtLink>

		<nav class="font-sans text-[10px] md:text-xs uppercase tracking-[0.2em] text-muted-ink flex flex-col md:flex-row gap-4 md:gap-8 text-center md:text-left">
			<NuxtLink to="/legal/mentions-legales" class="hover:text-brand transition-colors"> Mentions Légales </NuxtLink>
			<NuxtLink to="/legal/cgu" class="hover:text-brand transition-colors">CGU</NuxtLink>
			<NuxtLink to="/legal/confidentialite" class="hover:text-brand transition-colors"> Confidentialité </NuxtLink>
			<a href="mailto:contact@senlegal.sn" class="hover:text-brand transition-colors">Contact</a>
		</nav>

		<div class="font-sans text-[10px] md:text-xs text-muted-ink text-center md:text-right">© {{ year }} — Intelligence Juridique.</div>
	</footer>
</template>
