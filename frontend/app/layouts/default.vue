<template>
	<div class="min-h-[100dvh] flex flex-col bg-paper text-ink antialiased">
		<LayoutAppHeader />
		<main class="flex-1">
			<slot />
		</main>
		<LayoutAppFooter />
	</div>
</template>
