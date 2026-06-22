<script setup lang="ts">
import { ArrowUpRight } from "lucide-vue-next";
</script>

<template>
	<section id="tarifs" class="py-20 md:py-32 px-6 md:px-12 bg-white">
		<div class="max-w-[1200px] mx-auto">
			<div class="text-center mb-16 md:mb-24">
				<h2 class="font-serif text-3xl md:text-5xl text-ink mb-4 md:mb-6">Conditions d'accès</h2>
				<p class="font-sans text-muted-ink max-w-xl mx-auto text-base md:text-lg font-light">
					Une tarification transparente, pensée pour s'intégrer aux charges d'exploitation des cabinets et administrations.
				</p>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-0 border-t border-b border-rule md:divide-x divide-rule">
				<!-- Découverte -->
				<div class="p-8 sm:p-12 md:p-16 hover:bg-paper transition-colors border-b md:border-b-0 border-rule">
					<div class="font-sans text-[10px] md:text-xs uppercase tracking-widest text-brand mb-4 font-semibold">Édition I</div>
					<h3 class="font-serif text-3xl md:text-4xl text-ink mb-6 md:mb-8">Découverte.</h3>
					<div class="mb-8 md:mb-12 border-b border-rule pb-6 md:pb-8">
						<span class="font-serif text-xl md:text-2xl text-ink">Consultation Libre</span>
					</div>
					<ul class="space-y-4 md:space-y-6 mb-8 md:mb-12">
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-ink font-light">
							<span class="mt-1.5 md:mt-2 w-1 h-1 bg-brand rounded-full shrink-0" />
							5 consultations par jour
						</li>
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-ink font-light">
							<span class="mt-1.5 md:mt-2 w-1 h-1 bg-brand rounded-full shrink-0" />
							Accès intégral au Décret 2022-2295
						</li>
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-muted-ink font-light">
							<span class="mt-2.5 md:mt-3 w-3 md:w-4 h-px bg-rule shrink-0" />
							Pas d'analyse de documents PDF
						</li>
					</ul>
					<NuxtLink
						to="/login"
						class="inline-flex items-center gap-2 md:gap-3 font-sans text-[10px] md:text-xs tracking-[0.1em] uppercase pb-2 border-b border-ink text-ink hover:text-brand hover:border-brand transition-colors group font-semibold"
					>
						Explorer l'outil
						<ArrowUpRight :size="14" class="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
					</NuxtLink>
				</div>

				<!-- Cabinet -->
				<div class="p-8 sm:p-12 md:p-16 bg-brand text-paper relative">
					<div class="font-sans text-[10px] md:text-xs uppercase tracking-widest text-paper/70 mb-4 font-semibold">Édition II</div>
					<h3 class="font-serif text-3xl md:text-4xl text-white mb-6 md:mb-8">Cabinet.</h3>
					<div class="mb-8 md:mb-12 border-b border-paper/30 pb-6 md:pb-8 flex flex-wrap items-baseline gap-2">
						<span class="font-serif text-3xl md:text-4xl text-white">9 900</span>
						<span class="font-sans text-xs md:text-sm tracking-wide text-paper/80">FCFA / mois</span>
					</div>
					<ul class="space-y-4 md:space-y-6 mb-8 md:mb-12">
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-paper font-light">
							<span class="mt-1.5 md:mt-2 w-1 h-1 bg-paper rounded-full shrink-0" />
							Consultations et analyses illimitées
						</li>
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-paper font-light">
							<span class="mt-1.5 md:mt-2 w-1 h-1 bg-paper rounded-full shrink-0" />
							Import et coffre-fort 5 Go pour vos pièces
						</li>
						<li class="flex items-start gap-3 md:gap-4 text-sm md:text-base text-paper font-light">
							<span class="mt-1.5 md:mt-2 w-1 h-1 bg-paper rounded-full shrink-0" />
							Corpus juridique complet intégré
						</li>
					</ul>
					<NuxtLink
						to="/login?next=/dashboard/facturation"
						class="inline-flex items-center gap-2 md:gap-3 font-sans text-[10px] md:text-xs tracking-[0.1em] uppercase pb-2 border-b border-paper hover:text-ink hover:border-ink transition-colors group font-semibold"
					>
						Souscrire au plan
						<ArrowUpRight :size="14" class="group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
					</NuxtLink>
				</div>
			</div>
		</div>
	</section>
</template>
