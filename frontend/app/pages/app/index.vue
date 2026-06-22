<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { Menu, Send } from "lucide-vue-next";
import { motion } from "motion-v";
import { storeToRefs } from "pinia";
import { toast } from "vue-sonner";
import { useChatStore, type Citation, type Message } from "~/stores/chat";
import { useChatStream } from "~/composables/useChatStream";
import { useAppLayout } from "~/composables/useAppLayout";
import { apiErrorMessage } from "~/composables/useApi";

definePageMeta({ layout: "app" });

useSeoMeta({ title: "Consultation — SenLégal", robots: "noindex,nofollow" });

const route = useRoute();
const router = useRouter();
const chat = useChatStore();
const { currentMessages, isStreaming, current } = storeToRefs(chat);
const { send, abort } = useChatStream();
const { openSidebar } = useAppLayout();

const input = ref("");
const scrollEl = ref<HTMLElement | null>(null);

/** Vrai tant que l'utilisateur n'a pas scrollé manuellement vers le haut. */
const stickToBottom = ref(true);

function onScroll() {
	const el = scrollEl.value;
	if (!el) return;
	const distance = el.scrollHeight - (el.scrollTop + el.clientHeight);
	stickToBottom.value = distance < 80;
}

function scrollToBottom(behavior: ScrollBehavior = "smooth") {
	const el = scrollEl.value;
	if (!el) return;
	el.scrollTo({ top: el.scrollHeight, behavior });
}

/**
 * Cale le haut du dernier échange (question utilisateur) en haut du viewport,
 * pour que la réponse en cours de streaming reste visible sans être tirée
 * vers le bas à chaque token.
 */
async function pinLatestExchangeToTop() {
	await nextTick();
	const el = scrollEl.value;
	if (!el) return;
	const items = el.querySelectorAll("[data-msg]");
	if (items.length < 2) {
		scrollToBottom("auto");
		return;
	}
	const userMsg = items[items.length - 2] as HTMLElement;
	const top = userMsg.offsetTop - 16;
	el.scrollTo({ top, behavior: "smooth" });
	stickToBottom.value = false;
}

onMounted(async () => {
	if (!chat.conversations.length) await chat.fetchConversations();

	const convId = (route.query.conv as string) || (route.params.id as string | undefined);
	const q = (route.query.q as string)?.trim();

	if (convId) {
		await chat.selectConversation(convId).catch(() => {
			toast.error("Conversation introuvable.");
		});
	}

	if (q) {
		input.value = q;
		// purge le query param pour éviter resoumission au reload
		router.replace({ query: {} });
		await nextTick();
		submit();
	}
});

watch(
	currentMessages,
	async () => {
		if (!stickToBottom.value || isStreaming.value) return;
		await nextTick();
		scrollToBottom("smooth");
	},
	{ deep: true },
);

// Sur changement de conversation, force un scroll en bas et ramasse l'état « collé ».
watch(
	() => chat.currentId,
	async () => {
		stickToBottom.value = true;
		await nextTick();
		scrollToBottom("auto");
	},
);

const messages = computed<Message[]>(() => currentMessages.value);

async function submit() {
	const text = input.value.trim();
	if (!text || isStreaming.value) return;

	// Crée la conversation si nécessaire (premier message d'une session vierge).
	if (!chat.currentId) {
		try {
			await chat.createConversation();
		} catch (e) {
			toast.error(apiErrorMessage(e, "Impossible de créer la conversation."));
			return;
		}
	}
	const convId = chat.currentId!;

	chat.appendUserMessage(text);
	const placeholder = chat.appendAssistantPlaceholder();
	const placeholderLocalId = placeholder.localId!;
	input.value = "";
	isStreaming.value = true;
	// Cale la question en haut, la réponse va se dérouler en dessous
	// sans repousser la vue à chaque token.
	void pinLatestExchangeToTop();

	await send(convId, text, {
		onCitations: (citations: Citation[]) => chat.setCitations(placeholderLocalId, citations),
		onToken: (tok) => chat.appendToken(placeholderLocalId, tok),
		onDone: async (info) => {
			chat.finalizeAssistant(placeholderLocalId);
			chat.touchConversation(convId);
			if (info?.title) chat.applyAutoTitle(convId, info.title);
			isStreaming.value = false;
			// Récupère ids serveur des messages persistés.
			try {
				await chat.selectConversation(convId, { force: true });
			} catch {
				/* silencieux */
			}
		},
		onError: (err) => {
			chat.finalizeAssistant(placeholderLocalId, { error: true, errorMessage: err.message || "Erreur lors de la consultation." });
			isStreaming.value = false;
			toast.error(err.message || "La consultation a échoué.");
		},
	});
}

function stop() {
	abort();
	isStreaming.value = false;
	toast.info("Consultation interrompue.");
}

function onKey(e: KeyboardEvent) {
	if (e.key === "Enter" && !e.shiftKey) {
		e.preventDefault();
		submit();
	}
}

const headerTitle = computed(() => current.value?.title || "Consultation");

/** Texte exact renvoyé par l'IA quand elle ne dispose pas de l'information. */
const REFUSAL_TEXT = "Je ne dispose pas de cette information dans les textes juridiques sénégalais indexés.";

function isRefusal(content?: string | null): boolean {
	if (!content) return false;
	return content.trim().replaceAll(/\s+/g, " ") === REFUSAL_TEXT;
}
</script>

<template>
	<div class="flex flex-col h-full">
		<header class="h-16 md:h-20 border-b border-rule flex items-center justify-between px-4 md:px-8 shrink-0 bg-white z-10 gap-4">
			<div class="flex items-center gap-3 md:gap-4 min-w-0">
				<button class="md:hidden text-ink p-1 shrink-0" aria-label="Ouvrir le menu" @click="openSidebar">
					<Menu :size="20" />
				</button>
				<div class="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 truncate">
					<span class="font-serif text-lg md:text-2xl text-ink truncate">{{ headerTitle }}</span>
					<span class="text-[9px] md:text-[10px] uppercase tracking-widest text-brand font-semibold flex items-center gap-1.5 shrink-0">
						<span class="w-1.5 h-1.5 rounded-full bg-brand" />
						Décret 2022-2295
					</span>
				</div>
			</div>
		</header>

		<div ref="scrollEl" class="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth" @scroll.passive="onScroll">
			<div class="max-w-3xl mx-auto space-y-8 md:space-y-12 pb-8 md:pb-12">
				<div v-if="!messages.length && !isStreaming" class="text-center py-16">
					<p class="font-serif italic text-2xl md:text-3xl text-ink mb-4">La salle vous est ouverte.</p>
					<p class="text-sm text-muted-ink font-light max-w-md mx-auto">
						Posez une question juridique sur le droit sénégalais. Vos consultations sont archivées dans le panneau latéral.
					</p>
				</div>
				<motion.div
					v-for="msg in messages"
					:key="msg.localId || msg.id"
					data-msg
					:initial="{ opacity: 0, y: 10 }"
					:animate="{ opacity: 1, y: 0 }"
					:class="['flex flex-col', msg.role === 'USER' ? 'items-end' : 'items-start']"
				>
					<div class="text-[9px] md:text-[10px] uppercase tracking-widest text-muted-ink mb-1 md:mb-2 font-semibold">
						<span v-if="msg.role === 'ASSISTANT'" class="text-brand">SenLégal.</span>
						<span v-else>Le Consultant</span>
					</div>
					<div
						:class="[
							'max-w-[90%] md:max-w-[85%] text-sm md:text-lg leading-relaxed font-light',
							msg.role === 'USER' ? 'font-serif italic text-ink whitespace-pre-wrap' : 'font-sans text-ink border-l-2 border-brand pl-4 md:pl-6 py-1 md:py-2',
							msg.error ? 'text-destructive' : '',
						]"
					>
						<template v-if="msg.content">
							<ChatAssistantContent v-if="msg.role === 'ASSISTANT'" :content="msg.content" />
							<template v-else>{{ msg.content }}</template>
						</template>
						<span v-else-if="msg.pending" class="inline-flex gap-1 items-center text-muted-ink">
							<span class="w-1.5 h-1.5 bg-brand rounded-full animate-pulse" />
							<span class="w-1.5 h-1.5 bg-brand/70 rounded-full animate-pulse [animation-delay:120ms]" />
							<span class="w-1.5 h-1.5 bg-brand/40 rounded-full animate-pulse [animation-delay:240ms]" />
						</span>
					</div>
					<div v-if="msg.role === 'ASSISTANT' && msg.citations?.length && !isRefusal(msg.content)" class="w-full max-w-[90%] md:max-w-[85%]">
						<ChatCitationCard :citations="msg.citations" />
					</div>
				</motion.div>
			</div>
		</div>

		<div class="p-4 md:p-8 bg-white shrink-0 border-t border-rule">
			<div class="max-w-3xl mx-auto relative group">
				<div class="relative bg-paper border border-rule rounded-none overflow-hidden focus-within:border-brand transition-all flex flex-col">
					<textarea
						v-model="input"
						placeholder="Rédigez votre requête…"
						class="w-full resize-none bg-transparent px-4 pt-4 pb-14 md:px-6 md:pt-6 md:pb-16 outline-none text-sm md:text-base font-serif text-ink placeholder:text-muted-ink/50 placeholder:font-sans min-h-[90px] md:min-h-[120px]"
						@keydown="onKey"
					/>
					<div class="absolute bottom-2 left-2 right-2 md:bottom-4 md:left-4 md:right-4 flex justify-end items-center">
						<button
							v-if="isStreaming"
							type="button"
							class="px-4 py-2 md:px-6 md:py-2 text-[10px] md:text-xs uppercase tracking-widest font-semibold bg-transparent text-ink border border-ink hover:bg-ink hover:text-paper transition-colors"
							@click="stop"
						>
							Arrêter
						</button>
						<button
							v-else
							type="button"
							:disabled="!input.trim()"
							:class="[
								'px-4 py-2 md:px-6 md:py-2 text-[10px] md:text-xs uppercase tracking-widest font-semibold transition-all',
								input.trim() ? 'bg-brand text-paper hover:bg-brand-dark border border-brand' : 'bg-transparent text-muted-ink border border-rule cursor-not-allowed',
							]"
							@click="submit"
						>
							<span class="hidden sm:inline">Soumettre</span>
							<span class="sm:hidden"><Send :size="14" /></span>
						</button>
					</div>
				</div>
				<p class="text-center mt-3 md:mt-4 text-[8px] md:text-[10px] uppercase tracking-widest text-muted-ink px-4 leading-tight">
					Les analyses générées ne se substituent pas au conseil d'un expert.
				</p>
			</div>
		</div>
	</div>
</template>
