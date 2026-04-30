<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
	name?: string;
	initials?: string;
}>();

const display = computed(() => {
	if (props.initials) return props.initials.toUpperCase();
	if (!props.name) return "?";
	return props.name
		.split(" ")
		.map((p) => p[0])
		.filter(Boolean)
		.slice(0, 2)
		.join("")
		.toUpperCase();
});
</script>

<template>
	<span class="inline-flex items-center justify-center w-9 h-9 bg-brand-soft text-brand font-serif text-sm border border-brand/20">
		{{ display }}
	</span>
</template>
