<script setup lang="ts">
const features = [
	{ title: "Recherche Sémantique", desc: "Interrogation en langage naturel du Code de la Famille.", article: "Livres I à VIII", reliability: "Haute" },
	{ title: "Droit du Mariage", desc: "Conditions, régimes matrimoniaux, divorce et effets.", article: "Art. 108-199", reliability: "Absolue" },
	{ title: "Successions & Filiation", desc: "Droit commun et droit musulman, filiation, adoption.", article: "Art. 200-755", reliability: "Experte" },
	{ title: "Calcul des Délais", desc: "Planification des échéances légales (absence, tutelle).", article: "Art. 16-28", reliability: "Précise" },
];
</script>

<template>
	<section id="index" class="py-20 md:py-32 px-6 md:px-12 bg-paper">
		<div class="max-w-[1200px] mx-auto">
			<div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-12 md:mb-16 gap-6 md:gap-8 border-b border-brand pb-8 md:pb-12">
				<div>
					<div class="font-sans text-[10px] md:text-xs uppercase tracking-[0.3em] text-brand mb-4 md:mb-6 flex items-center gap-3 md:gap-4 font-semibold">
						<span class="w-8 md:w-12 h-px bg-brand" />
						Capacités Analytiques
					</div>
					<h2 class="font-serif text-4xl sm:text-5xl md:text-7xl tracking-tight leading-none text-ink">L'Index <span class="italic font-light text-brand">Légal</span>.</h2>
				</div>
				<p class="font-sans text-[10px] md:text-sm tracking-widest uppercase text-muted-ink max-w-[200px] md:max-w-xs md:text-right mt-2 md:mt-0">
					Inventaire des modules d'expertise disponibles.
				</p>
			</div>

			<div class="border-t border-rule">
				<LandingFeatureRow v-for="f in features" :key="f.title" :title="f.title" :desc="f.desc" :article="f.article" :reliability="f.reliability" />
			</div>
		</div>
	</section>
</template>
