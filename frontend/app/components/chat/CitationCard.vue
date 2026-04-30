<script setup lang="ts">
import type { Citation } from "~/stores/chat";

defineProps<{ citations: Citation[] }>();
</script>

<template>
	<div v-if="citations.length" class="mt-4 md:mt-6 space-y-3">
		<div class="text-[10px] uppercase tracking-[0.2em] text-muted-ink font-semibold flex items-center gap-2"><span class="w-4 h-px bg-muted-ink" /> Sources</div>
		<ul class="grid sm:grid-cols-2 gap-3">
			<li v-for="(c, i) in citations" :key="`${c.document}-${c.page}-${i}`" class="border border-rule p-4 bg-paper hover:border-brand transition-colors">
				<div class="flex items-baseline justify-between gap-2 mb-2">
					<span class="font-serif italic text-brand text-sm"> Article {{ c.article_number }} </span>
					<span class="text-[10px] uppercase tracking-widest text-muted-ink"> p. {{ c.page }} </span>
				</div>
				<p v-if="c.article_title" class="font-serif text-sm text-ink mb-2">{{ c.article_title }}</p>
				<p class="text-xs text-muted-ink font-light leading-relaxed line-clamp-3">{{ c.snippet }}</p>
				<div class="mt-2 text-[10px] uppercase tracking-widest text-muted-ink/80">
					{{ c.document }}<template v-if="c.score != null"> · {{ c.score.toFixed(2) }}</template>
				</div>
			</li>
		</ul>
	</div>
</template>
