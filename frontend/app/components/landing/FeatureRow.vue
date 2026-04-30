<script setup lang="ts">
defineProps<{
	title: string;
	desc: string;
	article: string;
	reliability: string;
}>();
</script>

<template>
	<div class="border-b border-rule py-6 md:py-8 grid grid-cols-12 gap-4 md:gap-8 items-baseline group hover:bg-paper transition-colors">
		<div class="col-span-12 sm:col-span-1 font-sans text-[10px] uppercase tracking-widest text-muted-ink">
			{{ article }}
		</div>
		<div class="col-span-12 sm:col-span-5">
			<h3 class="font-serif text-xl md:text-2xl text-ink group-hover:text-brand transition-colors">
				{{ title }}
			</h3>
		</div>
		<div class="col-span-8 sm:col-span-4 font-sans text-sm text-muted-ink font-light">
			{{ desc }}
		</div>
		<div class="col-span-4 sm:col-span-2 font-sans text-[10px] uppercase tracking-widest text-brand text-right font-semibold">
			{{ reliability }}
		</div>
	</div>
</template>
