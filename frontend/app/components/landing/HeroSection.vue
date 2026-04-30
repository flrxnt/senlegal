<script setup lang="ts">
import { ref } from "vue";
import { Scale } from "lucide-vue-next";
import { motion } from "motion-v";

const query = ref("");

function submit() {
	const q = query.value.trim();
	navigateTo({ path: "/app", query: q ? { q } : undefined });
}
</script>

<template>
	<section class="pt-6 pb-20 md:pt-10 md:pb-24 px-6 md:px-12">
		<div class="max-w-[1600px] mx-auto flex flex-col lg:flex-row gap-12 lg:gap-24 items-center">
			<div class="w-full lg:w-1/2 flex flex-col mt-4 md:mt-0">
				<motion.div
					:initial="{ opacity: 0, y: 10 }"
					:animate="{ opacity: 1, y: 0 }"
					:transition="{ duration: 1 }"
					class="font-sans text-[10px] md:text-xs uppercase tracking-[0.3em] text-brand mb-6 md:mb-8 flex items-center gap-3 md:gap-4 font-semibold"
				>
					<span class="w-6 md:w-8 h-px bg-brand" />
					Sénégal, Droit & Marchés
				</motion.div>

				<motion.h1
					:initial="{ opacity: 0, y: 20 }"
					:animate="{ opacity: 1, y: 0 }"
					:transition="{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }"
					class="font-serif text-[3.25rem] leading-[1] sm:text-[4.5rem] md:text-[5.5rem] lg:text-[6.5rem] md:leading-[0.95] tracking-tight text-ink"
				>
					L'art de la <br />
					<span class="italic font-light text-brand">commande</span> <br />
					publique.
				</motion.h1>

				<motion.p
					:initial="{ opacity: 0 }"
					:animate="{ opacity: 1 }"
					:transition="{ duration: 1, delay: 0.4 }"
					class="mt-6 md:mt-8 font-sans text-base md:text-lg font-light text-muted-ink max-w-md leading-relaxed"
				>
					Une expertise juridique instantanée, ancrée dans le Code des Marchés Publics (Décret 2022-2295) et la jurisprudence de l'ARCOP. La doctrine au service de l'action.
				</motion.p>

				<motion.form
					:initial="{ opacity: 0, y: 20 }"
					:animate="{ opacity: 1, y: 0 }"
					:transition="{ duration: 1, delay: 0.6 }"
					class="mt-12 md:mt-16 w-full max-w-lg border-b border-ink focus-within:border-brand pb-4 flex items-center gap-3 md:gap-4 group transition-colors"
					@submit.prevent="submit"
				>
					<Scale class="text-ink group-focus-within:text-brand transition-colors shrink-0" :size="20" :stroke-width="1.5" />
					<input
						v-model="query"
						type="text"
						placeholder="Interrogez le code…"
						aria-label="Interroger le code des marchés"
						class="w-full bg-transparent border-none outline-none font-serif text-lg md:text-xl placeholder:text-muted-ink/50 text-ink"
					/>
				</motion.form>

				<motion.div
					:initial="{ opacity: 0 }"
					:animate="{ opacity: 1 }"
					:transition="{ duration: 1, delay: 0.8 }"
					class="mt-4 md:mt-6 flex flex-wrap gap-x-4 gap-y-2 text-[10px] md:text-xs font-sans uppercase tracking-widest text-muted-ink"
				>
					Fréquent :
					<NuxtLink to="/app?q=Appel%20d'offres" class="text-brand cursor-pointer hover:underline underline-offset-4"> Appel d'offres </NuxtLink>
					,
					<NuxtLink to="/app?q=Avenant" class="text-brand cursor-pointer hover:underline underline-offset-4"> Avenant </NuxtLink>
				</motion.div>
			</div>

			<motion.div
				:initial="{ opacity: 0, scale: 0.95 }"
				:animate="{ opacity: 1, scale: 1 }"
				:transition="{ duration: 1.5, delay: 0.2, ease: 'easeOut' }"
				class="w-full lg:w-1/2 aspect-square sm:aspect-[4/5] lg:aspect-[3/4] relative group overflow-hidden mt-8 lg:mt-0"
			>
				<NuxtImg
					src="https://images.unsplash.com/photo-1729877218780-2036a20ffc64?auto=format&fit=crop&q=80&w=1080"
					alt="Architecture minimaliste abstraite"
					class="w-full h-full object-cover scale-105 group-hover:scale-100 transition-transform duration-1000 ease-out grayscale-[0.2]"
					loading="eager"
				/>
				<div class="absolute inset-0 bg-brand/0 group-hover:bg-brand/10 transition-colors duration-1000" />
				<div class="absolute inset-0 border border-white/20 m-4 pointer-events-none hidden md:block" />
				<div class="absolute bottom-4 left-4 right-4 md:right-auto md:bottom-8 md:left-8 bg-white/95 backdrop-blur-sm p-6 md:p-8 max-w-xs border border-rule/50">
					<p class="font-serif text-2xl md:text-3xl mb-1 md:mb-2 text-brand">100%</p>
					<p class="font-sans text-[10px] md:text-xs uppercase tracking-widest text-muted-ink leading-relaxed">Conformité avec les textes officiels du Sénégal.</p>
				</div>
			</motion.div>
		</div>
	</section>
</template>
