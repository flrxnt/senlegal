<script setup lang="ts">
import { ArrowRight } from "lucide-vue-next";

const props = defineProps<{ error: { statusCode: number; statusMessage?: string; message?: string } }>();

const code = computed(() => props.error?.statusCode || 500);
const isNotFound = computed(() => code.value === 404);
const heading = computed(() => (isNotFound.value ? "Article introuvable." : "Anomalie procédurale."));
const desc = computed(() => (isNotFound.value ? "La page demandée n'existe pas dans notre archive." : "Une erreur inattendue s'est produite lors de la consultation."));

function back() {
	clearError({ redirect: "/" });
}
</script>

<template>
	<div class="min-h-[100dvh] bg-paper text-ink flex flex-col items-center justify-center px-6 py-20 antialiased">
		<div class="font-sans text-[10px] uppercase tracking-[0.3em] text-brand mb-8 flex items-center gap-3 font-semibold">
			<span class="w-8 h-px bg-brand" />
			Erreur {{ code }}
		</div>
		<p class="font-serif text-[8rem] md:text-[14rem] leading-none text-brand italic font-light">
			{{ code }}
		</p>
		<h1 class="font-serif text-3xl md:text-5xl text-ink mt-6 md:mt-8 text-center">{{ heading }}</h1>
		<p class="font-sans text-muted-ink text-center max-w-md mt-4 md:mt-6 font-light">
			{{ desc }}
		</p>
		<button
			class="mt-12 inline-flex items-center gap-3 border border-ink text-ink px-8 py-4 font-sans text-xs uppercase tracking-widest font-semibold hover:bg-ink hover:text-paper transition-colors"
			@click="back"
		>
			Revenir à l'accueil
			<ArrowRight :size="14" />
		</button>
	</div>
</template>
