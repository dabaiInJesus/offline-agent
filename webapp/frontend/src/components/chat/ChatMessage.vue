<template>
  <div 
    class="flex"
    :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div 
      class="max-w-[80%] rounded-2xl px-4 py-3"
      :class="messageClass"
    >
      <!-- 头像 -->
      <div class="flex items-center space-x-2 mb-2">
        <div 
          class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium"
          :class="avatarClass"
        >
          {{ message.role === 'user' ? 'U' : 'AI' }}
        </div>
        <span class="text-xs text-gray-500">
          {{ formatTime(message.timestamp) }}
        </span>
      </div>

      <!-- 内容 -->
      <div class="markdown-body" v-html="renderedContent"></div>

      <!-- 来源（如果是知识库回答） -->
      <div v-if="message.sources && message.sources.length > 0" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
        <p class="text-xs text-gray-500 mb-2">来源:</p>
        <div class="space-y-1">
          <div 
            v-for="(source, index) in message.sources" 
            :key="index"
            class="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded"
          >
            {{ source.metadata?.source || '未知来源' }} 
            <span class="text-gray-400">(相似度: {{ (source.score * 100).toFixed(1) }}%)</span>
          </div>
        </div>
      </div>

      <!-- 执行步骤（如果是 Agent） -->
      <div v-if="message.executionSteps && message.executionSteps.length > 0" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
        <details>
          <summary class="text-xs text-gray-500 cursor-pointer">查看执行步骤 ({{ message.executionSteps.length }})</summary>
          <div class="mt-2 space-y-1 max-h-40 overflow-y-auto">
            <div 
              v-for="(step, index) in message.executionSteps" 
              :key="index"
              class="text-xs"
            >
              <span class="font-medium" :class="stepColor(step.role)">[{{ step.role }}]</span>
              <span class="text-gray-600 dark:text-gray-400">{{ step.content?.substring(0, 100) }}...</span>
            </div>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const messageClass = computed(() => {
  switch (props.message.role) {
    case 'user':
      return 'bg-primary-600 text-white'
    case 'assistant':
      return 'bg-white dark:bg-dark-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200'
    case 'error':
      return 'bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200'
    default:
      return 'bg-gray-100 dark:bg-gray-800'
  }
})

const avatarClass = computed(() => {
  switch (props.message.role) {
    case 'user':
      return 'bg-primary-700 text-white'
    case 'assistant':
      return 'bg-green-600 text-white'
    case 'error':
      return 'bg-red-600 text-white'
    default:
      return 'bg-gray-500 text-white'
  }
})

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  
  // 配置 marked
  marked.setOptions({
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value
      }
      return hljs.highlightAuto(code).value
    },
    breaks: true
  })
  
  return marked(props.message.content)
})

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const stepColor = (role) => {
  const colors = {
    'user': 'text-blue-600',
    'assistant': 'text-green-600',
    'observation': 'text-yellow-600',
    'tool': 'text-purple-600'
  }
  return colors[role] || 'text-gray-600'
}
</script>
