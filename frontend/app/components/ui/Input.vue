<script setup lang="ts">
import { cn } from "~/utils/cn";

defineOptions({ inheritAttrs: false });

const props = defineProps<{
	modelValue?: string | number;
	variant?: "underline" | "box";
}>();

const emit = defineEmits<{ "update:modelValue": [value: string] }>();

function onInput(e: Event) {
	emit("update:modelValue", (e.target as HTMLInputElement).value);
}

const variant = props.variant ?? "underline";
const variantClass = variant === "box" ? "bg-input-background border border-rule px-4 py-3 focus:border-brand" : "bg-transparent border-b border-rule px-0 py-3 focus:border-brand";
</script>

<template>
	<input
		:value="modelValue"
		@input="onInput"
		v-bind="$attrs"
		:class="cn('w-full font-sans text-sm text-ink placeholder:text-rule outline-none transition-colors', variantClass, ($attrs.class as string) || '')"
	/>
</template>
