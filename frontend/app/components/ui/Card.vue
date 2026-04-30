<script setup lang="ts">
import { cn } from "~/utils/cn";

defineOptions({ inheritAttrs: false });
</script>

<template>
	<div v-bind="$attrs" :class="cn('bg-white border border-rule p-6 md:p-8', ($attrs.class as string) || '')">
		<slot />
	</div>
</template>
