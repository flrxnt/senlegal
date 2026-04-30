<script setup lang="ts">
import { ref } from "vue";
import { onClickOutside, templateRef } from "@vueuse/core";

const open = ref(false);
const root = templateRef<HTMLElement>("root");

onClickOutside(root, () => (open.value = false));

function toggle() {
	open.value = !open.value;
}
</script>

<template>
	<div ref="root" class="relative inline-block">
		<slot name="trigger" :open="open" :toggle="toggle" />
		<Transition
			enter-active-class="transition duration-150 ease-out"
			leave-active-class="transition duration-100 ease-in"
			enter-from-class="opacity-0 -translate-y-1"
			leave-to-class="opacity-0 -translate-y-1"
		>
			<div v-if="open" class="absolute right-0 top-full mt-2 z-40 min-w-[200px] bg-white border border-rule shadow-lg py-2" @click="open = false">
				<slot :close="() => (open = false)" />
			</div>
		</Transition>
	</div>
</template>
