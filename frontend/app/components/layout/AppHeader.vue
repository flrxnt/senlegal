<script setup lang="ts">
import { ref } from "vue";
import { Menu, X } from "lucide-vue-next";

const open = ref(false);

const navLinks = [
	{ href: "/#doctrine", label: "La Doctrine" },
	{ href: "/#index", label: "L'Index" },
	{ href: "/#tarifs", label: "Tarifs" },
];
</script>

<template>
	<header class="w-full px-6 py-6 md:py-8 md:px-12 flex justify-between items-center bg-transparent relative z-30">
		<NuxtLink to="/" class="font-serif italic text-2xl tracking-wide text-brand"> SenLégal. </NuxtLink>

		<nav class="hidden md:flex items-center gap-12 font-sans text-xs uppercase tracking-[0.2em] text-ink">
			<a
				v-for="l in navLinks"
				:key="l.href"
				:href="l.href"
				class="hover:text-brand transition-colors relative after:content-[''] after:absolute after:w-0 after:h-px after:bg-brand after:left-0 after:-bottom-1 hover:after:w-full after:transition-all after:duration-300"
			>
				{{ l.label }}
			</a>
		</nav>

		<div class="hidden md:block">
			<UiButton to="/login" variant="outline" size="sm">Consultation</UiButton>
		</div>

		<button class="md:hidden text-ink p-2 -mr-2" :aria-label="open ? 'Fermer le menu' : 'Ouvrir le menu'" @click="open = true">
			<Menu :size="24" />
		</button>

		<UiSheet v-model:open="open" side="right" width="280px">
			<template #default="{ close }">
				<div class="p-6 border-b border-rule flex justify-between items-center">
					<span class="font-serif italic text-xl text-brand">SenLégal.</span>
					<button class="p-2 -mr-2 text-ink" aria-label="Fermer" @click="close">
						<X :size="20" />
					</button>
				</div>
				<nav class="flex-1 flex flex-col px-6 py-8 gap-6">
					<a v-for="l in navLinks" :key="l.href" :href="l.href" class="font-sans text-xs uppercase tracking-[0.2em] text-ink hover:text-brand transition-colors" @click="close">
						{{ l.label }}
					</a>
					<div class="pt-6 mt-2 border-t border-rule">
						<UiButton to="/login" variant="primary" size="md" class="w-full" @click="close"> Consultation </UiButton>
					</div>
				</nav>
			</template>
		</UiSheet>
	</header>
</template>
