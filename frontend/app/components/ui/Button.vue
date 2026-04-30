<script setup lang="ts">
import { computed } from "vue";
import { cn } from "~/utils/cn";

type Variant = "primary" | "secondary" | "outline" | "ghost" | "link" | "editorial";
type Size = "sm" | "md" | "lg" | "icon";

const props = withDefaults(
	defineProps<{
		variant?: Variant;
		size?: Size;
		type?: "button" | "submit" | "reset";
		disabled?: boolean;
		loading?: boolean;
		to?: string;
		href?: string;
	}>(),
	{ variant: "primary", size: "md", type: "button" },
);

const base =
	"inline-flex items-center justify-center gap-2 font-sans uppercase tracking-[0.15em] font-semibold transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed select-none whitespace-nowrap focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

const variants: Record<Variant, string> = {
	primary: "bg-brand text-paper hover:bg-brand-dark border border-brand",
	secondary: "bg-paper text-ink hover:bg-rule border border-rule",
	outline: "border border-brand text-brand hover:bg-brand hover:text-paper bg-transparent",
	ghost: "text-ink hover:text-brand bg-transparent",
	link: "text-brand hover:text-brand-dark border-b border-brand pb-0.5 px-0",
	editorial: "border border-ink text-ink hover:bg-ink hover:text-paper bg-transparent",
};

const sizes: Record<Size, string> = {
	sm: "text-[10px] px-4 py-2",
	md: "text-xs px-6 py-3",
	lg: "text-xs px-8 py-4",
	icon: "p-2 text-xs",
};

const tag = computed(() => (props.to ? resolveComponent("NuxtLink") : props.href ? "a" : "button"));
const classes = computed(() => cn(base, variants[props.variant], sizes[props.size]));
</script>

<template>
	<component :is="tag" :to="to" :href="href" :type="!to && !href ? type : undefined" :disabled="!to && !href ? disabled || loading : undefined" :class="classes">
		<slot />
	</component>
</template>
