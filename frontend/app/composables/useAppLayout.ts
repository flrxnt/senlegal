import { ref } from 'vue'

const sidebarOpen = ref(false)

export function useAppLayout() {
  return {
    sidebarOpen,
    openSidebar: () => (sidebarOpen.value = true),
    closeSidebar: () => (sidebarOpen.value = false),
    toggleSidebar: () => (sidebarOpen.value = !sidebarOpen.value),
  }
}
