<script setup lang="ts">
withDefaults(defineProps<{ orientation?: "horizontal" | "vertical" }>(), {
	orientation: "horizontal",
});
</script>

<template>
	<div :class="['bg-rule shrink-0', orientation === 'horizontal' ? 'h-px w-full' : 'w-px h-full']" role="separator" />
</template>
