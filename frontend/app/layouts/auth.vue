<script setup lang="ts">
import { ArrowRight } from "lucide-vue-next";
</script>

<template>
	<div class="min-h-[100dvh] bg-paper text-ink flex flex-col antialiased">
		<NuxtLink
			to="/"
			class="absolute top-6 left-6 md:top-8 md:left-8 flex items-center gap-2 text-muted-ink hover:text-brand transition-colors text-[10px] md:text-xs tracking-widest uppercase font-semibold z-10"
		>
			<ArrowRight :size="14" class="rotate-180" />
			<span class="hidden sm:inline">Retour</span>
		</NuxtLink>
		<main class="flex-1 flex items-center justify-center p-4 md:p-6">
			<slot />
		</main>
	</div>
</template>
