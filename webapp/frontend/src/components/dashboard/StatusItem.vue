<template>
  <div class="flex items-center justify-between py-3">
    <div class="flex items-center space-x-3">
      <div 
        class="w-3 h-3 rounded-full"
        :class="statusDotClass"
      ></div>
      <span class="font-medium text-gray-700 dark:text-gray-300">{{ name }}</span>
    </div>
    <span class="text-sm text-gray-500 dark:text-gray-400">{{ detail }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: String,
  status: {
    type: String,
    default: 'offline'
  },
  detail: String
})

const statusDotClass = computed(() => {
  switch (props.status) {
    case 'online':
      return 'bg-green-500'
    case 'offline':
      return 'bg-red-500'
    case 'warning':
      return 'bg-yellow-500'
    default:
      return 'bg-gray-400'
  }
})
</script>
