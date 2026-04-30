<script setup lang="ts">
import { onMounted, onUnmounted, watch } from "vue";
import { templateRef } from "@vueuse/core";
import { useFocusTrap } from "@vueuse/integrations/useFocusTrap";

const props = defineProps<{ open: boolean }>();
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
			<div v-if="open" class="fixed inset-0 z-50 grid place-items-center bg-ink/40 p-4" @click.self="close">
				<Transition appear enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 scale-95">
					<div ref="panel" class="bg-white border border-rule p-6 sm:p-10 max-w-md w-full" role="dialog" aria-modal="true">
						<slot :close="close" />
					</div>
				</Transition>
			</div>
		</Transition>
	</Teleport>
</template>
