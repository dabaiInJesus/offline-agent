<template>
  <header class="h-16 bg-white dark:bg-dark-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 sticky top-0 z-40">
    <!-- 左侧标题 -->
    <div class="flex items-center space-x-4">
      <h1 class="text-xl font-semibold text-gray-800 dark:text-white">
        {{ $route.meta.title || 'Offline Agent' }}
      </h1>
      <span 
        class="badge"
        :class="appStore.isInitialized ? 'badge-green' : 'badge-red'"
      >
        {{ appStore.isInitialized ? '运行中' : '未初始化' }}
      </span>
    </div>

    <!-- 右侧操作 -->
    <div class="flex items-center space-x-4">
      <!-- 通知按钮 -->
      <button class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
      </button>

      <!-- 主题切换 -->
      <button 
        @click="appStore.toggleDarkMode"
        class="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        :title="appStore.isDarkMode ? '切换到浅色模式' : '切换到深色模式'"
      >
        <svg v-if="appStore.isDarkMode" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>

      <!-- 用户头像 -->
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center text-white font-medium">
          U
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useAppStore } from '../../stores/app'

const appStore = useAppStore()
</script>
