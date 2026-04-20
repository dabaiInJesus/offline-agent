<template>
  <router-link :to="to" class="block p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200 group">
    <div class="flex items-center space-x-3">
      <div 
        class="w-10 h-10 rounded-lg flex items-center justify-center"
        :class="iconBgColor"
      >
        <component :is="icon" class="w-5 h-5" :class="iconColor" />
      </div>
      <div>
        <h4 class="font-medium text-gray-800 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">{{ name }}</h4>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ description }}</p>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: String,
  description: String,
  icon: Object,
  to: String,
  color: {
    type: String,
    default: 'blue'
  }
})

const colorMap = {
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', icon: 'text-blue-600' },
  green: { bg: 'bg-green-100 dark:bg-green-900/30', icon: 'text-green-600' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: 'text-purple-600' },
  yellow: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', icon: 'text-yellow-600' },
  red: { bg: 'bg-red-100 dark:bg-red-900/30', icon: 'text-red-600' }
}

const iconBgColor = computed(() => colorMap[props.color]?.bg || colorMap.blue.bg)
const iconColor = computed(() => colorMap[props.color]?.icon || colorMap.blue.icon)
</script>
