<script setup lang="ts">
import { onMounted, onUnmounted, watch } from "vue";
import { useFocusTrap } from "@vueuse/integrations/useFocusTrap";
import { templateRef } from "@vueuse/core";

const props = withDefaults(
	defineProps<{
		open: boolean;
		side?: "left" | "right";
		width?: string;
	}>(),
	{ side: "left", width: "320px" },
);

const emit = defineEmits<{ "update:open": [value: boolean] }>();

const panel = templateRef<HTMLElement>("panel");
const { activate, deactivate } = useFocusTrap(panel, { immediate: false });

watch(
	() => props.open,
	(v) => {
		if (typeof document === "undefined") return;
		document.body.style.overflow = v ? "hidden" : "";
		if (v) setTimeout(() => activate(), 50);
		else deactivate();
	},
);

function close() {
	emit("update:open", false);
}

function onKey(e: KeyboardEvent) {
	if (e.key === "Escape" && props.open) close();
}

onMounted(() => window.addEventListener("keydown", onKey));
onUnmounted(() => {
	window.removeEventListener("keydown", onKey);
	if (typeof document !== "undefined") document.body.style.overflow = "";
});
</script>

<template>
	<Teleport to="body">
		<Transition enter-active-class="transition-opacity duration-200" leave-active-class="transition-opacity duration-200" enter-from-class="opacity-0" leave-to-class="opacity-0">
			<div v-if="open" class="fixed inset-0 z-50 bg-ink/30 backdrop-blur-[2px]" @click="close" />
		</Transition>
		<Transition
			enter-active-class="transition-transform duration-300 ease-out"
			leave-active-class="transition-transform duration-300 ease-in"
			:enter-from-class="side === 'left' ? '-translate-x-full' : 'translate-x-full'"
			:leave-to-class="side === 'left' ? '-translate-x-full' : 'translate-x-full'"
		>
			<aside
				v-if="open"
				ref="panel"
				:class="['fixed inset-y-0 z-50 bg-paper border-rule flex flex-col shadow-xl', side === 'left' ? 'left-0 border-r' : 'right-0 border-l']"
				:style="{ width }"
				role="dialog"
				aria-modal="true"
			>
				<slot :close="close" />
			</aside>
		</Transition>
	</Teleport>
</template>
