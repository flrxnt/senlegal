<script setup lang="ts">
import { useAppLayout } from "~/composables/useAppLayout";

const { sidebarOpen } = useAppLayout();
</script>

<template>
	<div class="h-[100dvh] w-full bg-white flex font-sans overflow-hidden relative">
		<aside class="hidden md:flex w-[300px] shrink-0">
			<LayoutAppSidebar />
		</aside>

		<UiSheet v-model:open="sidebarOpen" side="left" width="280px">
			<template #default="{ close }">
				<LayoutAppSidebar :mobile-open="true" @close-mobile="close" />
			</template>
		</UiSheet>

		<div class="flex-1 flex flex-col min-w-0 bg-white w-full">
			<slot />
		</div>
	</div>
</template>
