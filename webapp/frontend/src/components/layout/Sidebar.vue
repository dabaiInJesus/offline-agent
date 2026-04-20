<template>
  <aside 
    class="fixed left-0 top-0 h-full bg-white dark:bg-dark-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 z-50"
    :class="{ 'w-64': !collapsed, 'w-16': collapsed }"
  >
    <!-- Logo -->
    <div class="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <span v-if="!collapsed" class="text-lg font-bold text-gray-800 dark:text-white">Offline Agent</span>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="p-4 space-y-2">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 group"
        :class="[
          $route.path === item.path 
            ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400' 
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
        ]"
      >
        <component 
          :is="item.icon" 
          class="w-5 h-5 flex-shrink-0"
          :class="$route.path === item.path ? 'text-primary-600 dark:text-primary-400' : 'group-hover:text-gray-900 dark:group-hover:text-white'"
        />
        <span v-if="!collapsed" class="font-medium">{{ item.name }}</span>
      </router-link>
    </nav>

    <!-- 底部操作栏 -->
    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
      <button
        @click="appStore.toggleSidebar"
        class="w-full flex items-center justify-center p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        :title="collapsed ? '展开' : '收起'"
      >
        <svg 
          class="w-5 h-5 transition-transform duration-300"
          :class="{ 'rotate-180': collapsed }"
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '../../stores/app'
import {
  HomeIcon,
  ChatBubbleLeftRightIcon,
  CircleStackIcon,
  BookOpenIcon,
  CpuChipIcon,
  WrenchScrewdriverIcon,
  Cog6ToothIcon
} from '@heroicons/vue/24/outline'

const appStore = useAppStore()
const collapsed = computed(() => appStore.sidebarCollapsed)

const menuItems = [
  { name: '控制台', path: '/', icon: HomeIcon },
  { name: '对话', path: '/chat', icon: ChatBubbleLeftRightIcon },
  { name: '数据库', path: '/database', icon: CircleStackIcon },
  { name: '知识库', path: '/knowledge-base', icon: BookOpenIcon },
  { name: '智能体', path: '/agent', icon: CpuChipIcon },
  { name: '技能', path: '/skills', icon: WrenchScrewdriverIcon },
  { name: '设置', path: '/settings', icon: Cog6ToothIcon }
]
</script>
