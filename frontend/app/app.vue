<script setup lang="ts">
import { Toaster } from "vue-sonner";
</script>

<template>
	<div>
		<NuxtRouteAnnouncer />
		<NuxtLayout>
			<NuxtPage />
		</NuxtLayout>
		<Toaster position="top-right" :toast-options="{ class: 'font-sans' }" rich-colors />
	</div>
</template>
