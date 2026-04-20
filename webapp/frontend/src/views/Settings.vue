<template>
  <div class="space-y-6">
    <div class="card p-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">系统设置</h2>

      <!-- 外观设置 -->
      <div class="mb-8">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">外观</h3>
        <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div class="flex items-center space-x-3">
            <svg v-if="appStore.isDarkMode" class="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <svg v-else class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
            <span class="font-medium text-gray-700 dark:text-gray-300">深色模式</span>
          </div>
          <button
            @click="appStore.toggleDarkMode"
            class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
            :class="appStore.isDarkMode ? 'bg-primary-600' : 'bg-gray-300'"
          >
            <span
              class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
              :class="appStore.isDarkMode ? 'translate-x-6' : 'translate-x-1'"
            ></span>
          </button>
        </div>
      </div>

      <!-- 系统信息 -->
      <div class="mb-8">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">系统信息</h3>
        <div class="space-y-3">
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <span class="text-gray-600 dark:text-gray-400">版本</span>
            <span class="font-medium text-gray-800 dark:text-white">1.0.0</span>
          </div>
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <span class="text-gray-600 dark:text-gray-400">系统状态</span>
            <span class="font-medium" :class="appStore.isInitialized ? 'text-green-600' : 'text-yellow-600'">
              {{ appStore.isInitialized ? '已初始化' : '初始化中...' }}
            </span>
          </div>
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <span class="text-gray-600 dark:text-gray-400">后端地址</span>
            <span class="font-medium text-gray-800 dark:text-white">http://localhost:8000</span>
          </div>
          <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <span class="text-gray-600 dark:text-gray-400">API 文档</span>
            <a href="http://localhost:8000/docs" target="_blank" class="font-medium text-primary-600 hover:text-primary-700">http://localhost:8000/docs</a>
          </div>
        </div>
      </div>

      <!-- 技术栈 -->
      <div>
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">技术栈</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div v-for="tech in techStack" :key="tech.name" class="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
            <div class="text-sm font-medium text-gray-800 dark:text-white">{{ tech.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ tech.desc }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAppStore } from '../stores/app'

const appStore = useAppStore()

const techStack = [
  { name: 'LangChain', desc: 'AI 应用框架' },
  { name: 'LangGraph', desc: '图式 Agent' },
  { name: 'Ollama', desc: '本地大模型' },
  { name: 'FastAPI', desc: '后端框架' },
  { name: 'Vue 3', desc: '前端框架' },
  { name: 'TailwindCSS', desc: 'CSS 框架' },
  { name: 'Pinia', desc: '状态管理' },
  { name: 'ChromaDB', desc: '向量数据库' }
]
</script>
