<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ variant?: "brand" | "neutral" | "outline" }>(), { variant: "brand" });

const cls = computed(() => {
	switch (props.variant) {
		case "neutral":
			return "bg-paper text-ink border border-rule";
		case "outline":
			return "bg-transparent text-brand border border-brand";
		default:
			return "bg-brand-soft text-brand border border-brand/20";
	}
});
</script>

<template>
	<span :class="['inline-flex items-center gap-1.5 px-2 py-1 text-[10px] uppercase tracking-widest font-semibold', cls]">
		<slot />
	</span>
</template>
