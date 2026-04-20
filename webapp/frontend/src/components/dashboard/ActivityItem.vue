<template>
  <div class="flex items-start space-x-3 py-3">
    <div 
      class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
      :class="typeBgClass"
    >
      <component :is="typeIcon" class="w-4 h-4" :class="typeIconClass" />
    </div>
    <div class="flex-1 min-w-0">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-medium text-gray-800 dark:text-white">{{ title }}</h4>
        <span class="text-xs text-gray-400 flex-shrink-0 ml-2">{{ time }}</span>
      </div>
      <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{{ description }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ChatBubbleLeftRightIcon, CircleStackIcon, BookOpenIcon, WrenchIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  type: String,
  title: String,
  time: String,
  description: String
})

const typeConfig = {
  chat: { bg: 'bg-blue-100 dark:bg-blue-900/30', icon: ChatBubbleLeftRightIcon, iconClass: 'text-blue-600' },
  database: { bg: 'bg-green-100 dark:bg-green-900/30', icon: CircleStackIcon, iconClass: 'text-green-600' },
  kb: { bg: 'bg-purple-100 dark:bg-purple-900/30', icon: BookOpenIcon, iconClass: 'text-purple-600' },
  skill: { bg: 'bg-yellow-100 dark:bg-yellow-900/30', icon: WrenchIcon, iconClass: 'text-yellow-600' }
}

const typeBgClass = computed(() => typeConfig[props.type]?.bg || typeConfig.chat.bg)
const typeIcon = computed(() => typeConfig[props.type]?.icon || ChatBubbleLeftRightIcon)
const typeIconClass = computed(() => typeConfig[props.type]?.iconClass || typeConfig.chat.iconClass)
</script>
