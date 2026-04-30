<script setup lang="ts">
defineOptions({ inheritAttrs: false });
</script>

<template>
	<label v-bind="$attrs" class="block text-[10px] md:text-xs font-medium text-ink mb-2 uppercase tracking-widest">
		<slot />
	</label>
</template>
