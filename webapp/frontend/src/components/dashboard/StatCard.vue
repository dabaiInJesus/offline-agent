<template>
  <div class="card p-6 hover:shadow-md transition-shadow">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm font-medium text-gray-600 dark:text-gray-400">{{ title }}</p>
        <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ value }}</p>
        <p v-if="trend" class="text-sm mt-2" :class="trendColor">{{ trend }}</p>
      </div>
      <div 
        class="w-12 h-12 rounded-xl flex items-center justify-center"
        :class="iconBgColor"
      >
        <component :is="icon" class="w-6 h-6" :class="iconColor" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: String,
  value: String,
  icon: Object,
  color: {
    type: String,
    default: 'blue'
  },
  trend: String
})

const colorMap = {
  blue: { bg: 'bg-blue-100 dark:bg-blue-900/30', icon: 'text-blue-600', trend: 'text-blue-600' },
  green: { bg: 'bg-green-100 dark:bg-green-900/30', icon: 'text-green-600', trend: 'text-green-600' },
  purple: { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: 'text-purple-600', trend: 'text-purple-600' },
  yellow: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', icon: 'text-yellow-600', trend: 'text-yellow-600' },
  red: { bg: 'bg-red-100 dark:bg-red-900/30', icon: 'text-red-600', trend: 'text-red-600' }
}

const iconBgColor = computed(() => colorMap[props.color]?.bg || colorMap.blue.bg)
const iconColor = computed(() => colorMap[props.color]?.icon || colorMap.blue.icon)
const trendColor = computed(() => colorMap[props.color]?.trend || colorMap.blue.trend)
</script>
