<script setup lang="ts">
import { cn } from "~/utils/cn";

defineOptions({ inheritAttrs: false });

defineProps<{ modelValue?: string }>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

function onInput(e: Event) {
	emit("update:modelValue", (e.target as HTMLTextAreaElement).value);
}
</script>

<template>
	<textarea
		:value="modelValue"
		@input="onInput"
		v-bind="$attrs"
		:class="cn('w-full resize-none bg-transparent outline-none font-serif text-base text-ink placeholder:text-muted-ink/60 placeholder:font-sans', ($attrs.class as string) || '')"
	/>
</template>
