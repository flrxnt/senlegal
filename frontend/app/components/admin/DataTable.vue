<script setup lang="ts" generic="T">
interface Column<R> {
	key: string;
	label: string;
	span?: number;
	format?: (row: R) => string;
}

const props = defineProps<{
	columns: Column<T>[];
	rows: T[];
	loading?: boolean;
	total?: number;
	skip: number;
	take: number;
	emptyLabel?: string;
}>();

const emit = defineEmits<{
	(e: "update:skip", v: number): void;
	(e: "row-click", row: T): void;
}>();

function totalSpan() {
	return props.columns.reduce((s, c) => s + (c.span ?? 1), 0);
}

function prev() {
	emit("update:skip", Math.max(0, props.skip - props.take));
}
function next() {
	if (props.total !== undefined && props.skip + props.take >= props.total) return;
	emit("update:skip", props.skip + props.take);
}
</script>

<template>
	<div>
		<div
			class="border-t border-b border-rule grid items-baseline px-2 py-3 text-[10px] uppercase tracking-widest text-muted-ink font-semibold"
			:style="{ gridTemplateColumns: `repeat(${totalSpan()}, minmax(0,1fr))` }"
		>
			<div v-for="c in columns" :key="c.key" :style="{ gridColumn: `span ${c.span ?? 1} / span ${c.span ?? 1}` }">
				{{ c.label }}
			</div>
		</div>

		<p v-if="loading" class="text-xs uppercase tracking-widest text-muted-ink py-8">Chargement…</p>

		<div v-else-if="!rows.length" class="border-b border-rule py-12 text-center text-muted-ink font-serif italic">
			{{ emptyLabel || "Aucun résultat." }}
		</div>

		<button
			v-for="(row, idx) in rows"
			v-else
			:key="idx"
			type="button"
			class="border-b border-rule grid items-center px-2 py-4 text-left text-sm w-full hover:bg-paper transition-colors"
			:style="{ gridTemplateColumns: `repeat(${totalSpan()}, minmax(0,1fr))` }"
			@click="emit('row-click', row)"
		>
			<div
				v-for="c in columns"
				:key="c.key"
				class="font-sans text-ink truncate pr-3"
				:style="{ gridColumn: `span ${c.span ?? 1} / span ${c.span ?? 1}` }"
			>
				<slot :name="c.key" :row="row" :value="c.format ? c.format(row) : (row as Record<string, unknown>)[c.key]">
					{{ c.format ? c.format(row) : (row as Record<string, unknown>)[c.key] }}
				</slot>
			</div>
		</button>

		<div v-if="total !== undefined" class="flex items-center justify-between mt-6 text-[10px] uppercase tracking-widest text-muted-ink">
			<button class="hover:text-brand disabled:opacity-30" :disabled="skip === 0" @click="prev">← Précédent</button>
			<span>
				{{ rows.length ? `${skip + 1}–${skip + rows.length}` : "0" }} sur {{ total }}
			</span>
			<button class="hover:text-brand disabled:opacity-30" :disabled="skip + take >= total" @click="next">Suivant →</button>
		</div>
	</div>
</template>
