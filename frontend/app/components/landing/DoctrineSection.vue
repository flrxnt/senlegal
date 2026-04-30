<template>
	<section id="doctrine" class="py-20 md:py-32 px-6 md:px-12 bg-brand text-paper">
		<div class="max-w-[1600px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-center">
			<div class="relative aspect-[4/3] overflow-hidden bg-brand-dark">
				<NuxtImg
					src="https://images.unsplash.com/photo-1618751620143-4d854c70f726?auto=format&fit=crop&q=80&w=1080"
					alt="Cabinet épuré"
					class="w-full h-full object-cover opacity-40 mix-blend-luminosity grayscale"
				/>
				<div class="absolute inset-0 flex items-center justify-center p-8 md:p-12 text-center bg-brand/20">
					<h3 class="font-serif text-3xl sm:text-4xl md:text-5xl lg:text-6xl italic font-light text-white leading-tight">
						« La sécurité juridique <br class="hidden sm:block" />n'est pas une option, <br />c'est le fondement. »
					</h3>
				</div>
			</div>

			<div class="flex flex-col justify-center max-w-xl">
				<h2 class="font-serif text-4xl md:text-5xl mb-6 md:mb-8 text-white">La rigueur <br class="md:hidden" /><span class="italic text-paper/70">augmentée</span>.</h2>
				<p class="font-sans text-paper/90 font-light text-base md:text-lg mb-10 md:mb-12 leading-relaxed">
					Nous avons pensé SenLégal non pas comme un outil technologique, mais comme un collaborateur intellectuel. Il compulse la réglementation, identifie les pièges procéduraux
					et rédige les clauses administratives avec l'exigence d'un expert.
				</p>

				<div class="space-y-6 md:space-y-8 border-t border-paper/30 pt-8">
					<div>
						<h4 class="font-sans text-[10px] md:text-xs uppercase tracking-[0.2em] text-paper/60 mb-2 font-medium">01 — L'Analyse</h4>
						<p class="font-serif text-xl md:text-2xl text-white">Lecture approfondie des Dossiers d'Appel d'Offres (DAO) et détection des failles.</p>
					</div>
					<div>
						<h4 class="font-sans text-[10px] md:text-xs uppercase tracking-[0.2em] text-paper/60 mb-2 font-medium">02 — La Rédaction</h4>
						<p class="font-serif text-xl md:text-2xl text-white">Génération de rapports d'évaluation, lettres de notification et réponses aux recours.</p>
					</div>
				</div>

				<NuxtLink
					to="/login"
					class="mt-12 md:mt-16 bg-paper text-brand px-8 py-4 font-sans text-[10px] md:text-xs uppercase tracking-widest font-semibold hover:bg-white transition-colors w-fit text-center"
				>
					Initier une consultation
				</NuxtLink>
			</div>
		</div>
	</section>
</template>
