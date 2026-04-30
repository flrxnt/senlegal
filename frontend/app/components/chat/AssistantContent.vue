<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ content: string }>();

/**
 * Mini-rendu Markdown (sans dépendance externe) :
 *  - échappement HTML d'abord
 *  - gras **x**, italique *x*, code `x`
 *  - titres # / ## / ###
 *  - listes - / * / 1. 2.
 *  - paragraphes / sauts de ligne
 *  - mise en valeur des citations [Article X — document, p. N]
 */

function escapeHtml(s: string): string {
	return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function inline(text: string): string {
	let out = text;
	// code spans `code`
	out = out.replace(/`([^`]+?)`/g, '<code class="px-1 py-0.5 bg-rule/40 text-[0.92em] font-mono">$1</code>');
	// bold **x**
	out = out.replace(/\*\*([^*]+?)\*\*/g, "<strong>$1</strong>");
	// italic *x*  (pas si déjà dans bold)
	out = out.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, "$1<em>$2</em>");
	// liens [label](url)
	out = out.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-brand underline">$1</a>');
	// citations [Article X — Document, p. N]  -> vert + gras
	out = out.replace(/\[(Article\s+[^\]]+?)\]/gi, '<strong class="text-brand">[$1]</strong>');
	return out;
}

function renderMarkdown(src: string): string {
	const lines = escapeHtml(src.replace(/\r\n/g, "\n")).split("\n");
	const html: string[] = [];
	let i = 0;
	let para: string[] = [];

	const flushPara = () => {
		if (para.length === 0) return;
		html.push(`<p>${inline(para.join(" "))}</p>`);
		para = [];
	};

	while (i < lines.length) {
		const line = lines[i] ?? "";
		// Titres
		const h = /^(#{1,3})\s+(.*)$/.exec(line);
		if (h) {
			flushPara();
			const lvl = h[1]?.length ?? 1;
			const tag = `h${Math.min(lvl + 2, 6)}`; // h3/h4/h5
			html.push(`<${tag} class="font-serif text-ink mt-4 mb-2">${inline(h[2] ?? "")}</${tag}>`);
			i++;
			continue;
		}
		// Listes
		if (/^\s*([-*]|\d+\.)\s+/.test(line)) {
			flushPara();
			const ordered = /^\s*\d+\.\s+/.test(line);
			const items: string[] = [];
			while (i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i] ?? "")) {
				const itemText = (lines[i] ?? "").replace(/^\s*([-*]|\d+\.)\s+/, "");
				items.push(`<li>${inline(itemText)}</li>`);
				i++;
			}
			const tag = ordered ? "ol" : "ul";
			const cls = ordered ? "list-decimal pl-6 my-3 space-y-1" : "list-disc pl-6 my-3 space-y-1";
			html.push(`<${tag} class="${cls}">${items.join("")}</${tag}>`);
			continue;
		}
		// Ligne vide => fin de paragraphe
		if (line.trim() === "") {
			flushPara();
			i++;
			continue;
		}
		para.push(line.trim());
		i++;
	}
	flushPara();
	return html.join("\n");
}

const html = computed(() => renderMarkdown(props.content || ""));
</script>

<template>
	<div class="prose-senlegal" v-html="html" />
</template>

<style scoped>
.prose-senlegal :deep(p) {
	margin: 0.5em 0;
}
.prose-senlegal :deep(p:first-child) {
	margin-top: 0;
}
.prose-senlegal :deep(p:last-child) {
	margin-bottom: 0;
}
.prose-senlegal :deep(strong) {
	font-weight: 600;
}
.prose-senlegal :deep(em) {
	font-style: italic;
}
</style>
