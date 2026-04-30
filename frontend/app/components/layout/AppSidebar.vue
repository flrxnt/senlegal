<script setup lang="ts">
import { LogOut, PenTool, X, User as UserIcon, Trash2, Pencil, ShieldCheck } from "lucide-vue-next";
import { storeToRefs } from "pinia";
import { toast } from "vue-sonner";
import { useAuthStore } from "~/stores/auth";
import { useChatStore } from "~/stores/chat";
import { apiErrorMessage } from "~/composables/useApi";
import { planLabel } from "~/utils/plan";

defineProps<{ mobileOpen?: boolean }>();
const emit = defineEmits<{ "close-mobile": [] }>();

const authStore = useAuthStore();
const chatStore = useChatStore();
const { user, isAdmin } = storeToRefs(authStore);
const { conversations, currentId } = storeToRefs(chatStore);

onMounted(async () => {
	if (authStore.isAuthenticated && conversations.value.length === 0) {
		try {
			await chatStore.fetchConversations();
		} catch {
			/* silencieux */
		}
	}
});

async function startNew() {
	try {
		await chatStore.createConversation();
		await navigateTo("/app");
		emit("close-mobile");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Impossible de créer la conversation."));
	}
}

async function select(id: string) {
	try {
		await chatStore.selectConversation(id);
		await navigateTo({ path: "/app", query: { conv: id } });
		emit("close-mobile");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Conversation introuvable."));
	}
}

async function rename(id: string, currentTitle: string) {
	const next = globalThis.prompt("Renommer cette consultation", currentTitle);
	if (!next || next.trim() === currentTitle) return;
	try {
		await chatStore.renameConversation(id, next.trim());
		toast.success("Consultation renommée.");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Renommage impossible."));
	}
}

async function remove(id: string, title: string) {
	if (!globalThis.confirm(`Supprimer définitivement « ${title || "cette consultation"} » ?`)) return;
	try {
		await chatStore.deleteConversation(id);
		toast.success("Consultation supprimée.");
		await navigateTo("/app");
	} catch (e) {
		toast.error(apiErrorMessage(e, "Suppression impossible."));
	}
}

async function logout() {
	await authStore.logout();
	chatStore.reset();
	await navigateTo("/login");
}

function formatDate(iso: string) {
	return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" });
}
</script>

<template>
	<div class="h-full w-full bg-paper border-r border-rule flex flex-col">
		<div class="p-6 border-b border-rule flex justify-between items-center md:block">
			<NuxtLink to="/" class="font-serif italic text-xl md:text-2xl text-brand md:mb-8 md:block"> SenLégal. </NuxtLink>
			<button v-if="mobileOpen" class="md:hidden text-ink p-1 -mr-1" aria-label="Fermer" @click="emit('close-mobile')">
				<X :size="20" />
			</button>
			<button
				class="hidden md:flex w-full bg-transparent border border-brand text-brand items-center justify-between px-4 py-3 text-xs tracking-widest uppercase font-semibold hover:bg-brand hover:text-paper transition-colors"
				@click="startNew"
			>
				Nouveau Dossier
				<PenTool :size="14" />
			</button>
		</div>

		<div class="p-4 md:hidden border-b border-rule">
			<button class="w-full bg-brand text-paper flex items-center justify-center gap-2 px-4 py-3 text-[10px] tracking-widest uppercase font-semibold" @click="startNew">
				Nouveau Dossier <PenTool :size="14" />
			</button>
		</div>

		<div class="flex-1 overflow-y-auto p-6">
			<div class="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-ink mb-4 md:mb-6 flex items-center gap-2">
				<span class="w-4 h-px bg-muted-ink" />
				Archives
			</div>
			<p v-if="conversations.length === 0" class="text-xs text-muted-ink font-light italic">Aucun dossier. Créez votre première consultation.</p>
			<ul v-else class="space-y-4">
				<li v-for="c in conversations" :key="c.id" class="group/item">
					<div
						class="border-l-2 pl-3 -ml-3 transition-colors flex items-start justify-between gap-2"
						:class="c.id === currentId ? 'border-brand' : 'border-transparent hover:border-brand'"
					>
						<button type="button" class="text-left flex-1 min-w-0" @click="select(c.id)">
							<div class="text-sm font-serif text-ink truncate" :class="c.id === currentId ? 'italic text-brand' : 'group-hover/item:italic group-hover/item:text-brand'">
								{{ c.title || "Nouveau dossier" }}
							</div>
							<div class="text-[10px] uppercase tracking-widest text-muted-ink mt-1 flex items-center gap-2">
								<span>{{ formatDate(c.updatedAt) }}</span>
								<span v-if="c._count?.messages" class="text-muted-ink/60">· {{ c._count.messages }} msg</span>
							</div>
						</button>
						<div class="flex items-center gap-1 opacity-0 group-hover/item:opacity-100 transition-opacity shrink-0">
							<button class="text-muted-ink hover:text-brand p-1" :aria-label="`Renommer ${c.title}`" @click="rename(c.id, c.title)">
								<Pencil :size="13" />
							</button>
							<button class="text-muted-ink hover:text-destructive p-1" :aria-label="`Supprimer ${c.title}`" @click="remove(c.id, c.title)">
								<Trash2 :size="13" />
							</button>
						</div>
					</div>
				</li>
			</ul>

			<NuxtLink
				v-if="isAdmin"
				to="/admin"
				class="mt-8 flex items-center gap-2 text-[10px] uppercase tracking-widest font-semibold text-brand hover:text-brand-dark border-t border-rule pt-6"
			>
				<ShieldCheck :size="14" />
				Console administrateur
			</NuxtLink>
		</div>

		<div class="p-6 border-t border-rule bg-paper">
			<div class="flex items-center justify-between gap-3">
				<div class="text-left min-w-0">
					<div class="font-serif text-base md:text-lg text-ink truncate">
						{{ user?.name || user?.email || "Invité" }}
					</div>
					<div class="text-[10px] tracking-widest uppercase text-brand font-semibold">
						{{ planLabel(user?.plan) }}
					</div>
				</div>
				<div class="flex items-center gap-1 shrink-0">
					<NuxtLink to="/dashboard" class="text-muted-ink hover:text-brand transition-colors p-2" title="Tableau de bord" aria-label="Tableau de bord">
						<UserIcon :size="18" :stroke-width="1.5" />
					</NuxtLink>
					<button class="text-muted-ink hover:text-brand transition-colors p-2 -mr-2" title="Quitter la salle" aria-label="Se déconnecter" @click="logout">
						<LogOut :size="18" :stroke-width="1.5" />
					</button>
				</div>
			</div>
		</div>
	</div>
</template>
