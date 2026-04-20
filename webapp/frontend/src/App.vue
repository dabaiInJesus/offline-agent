<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-900 transition-colors duration-200">
    <Sidebar />
    <div 
      class="transition-all duration-300"
      :class="{ 
        'ml-64': !appStore.sidebarCollapsed, 
        'ml-16': appStore.sidebarCollapsed 
      }"
    >
      <TopBar />
      <main class="p-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAppStore } from './stores/app'
import Sidebar from './components/layout/Sidebar.vue'
import TopBar from './components/layout/TopBar.vue'

const appStore = useAppStore()

onMounted(() => {
  appStore.initDarkMode()
  appStore.fetchStatus()
})
</script>

<style>
/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
