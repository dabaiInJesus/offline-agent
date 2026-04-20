import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useChatStore = defineStore('chat', () => {
  // State
  const messages = ref([])
  const currentConversation = ref(null)
  const loading = ref(false)
  const streaming = ref(false)
  const error = ref(null)

  // Settings
  const settings = ref({
    agentType: 'react',
    useKnowledgeBase: null,
    useDatabase: null
  })

  // Getters
  const messageCount = computed(() => messages.value.length)
  const hasMessages = computed(() => messages.value.length > 0)

  // Actions
  const sendMessage = async (content) => {
    if (!content.trim()) return

    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    }
    messages.value.push(userMessage)

    loading.value = true
    error.value = null

    try {
      const response = await axios.post('/api/chat', {
        message: content,
        agent_type: settings.value.agentType,
        use_knowledge_base: settings.value.useKnowledgeBase,
        use_database: settings.value.useDatabase
      })

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources,
        executionSteps: response.data.execution_steps,
        timestamp: new Date().toISOString()
      }
      messages.value.push(assistantMessage)

      return response.data
    } catch (err) {
      error.value = err.message || '发送消息失败'
      const errorMessage = {
        id: Date.now() + 1,
        role: 'error',
        content: error.value,
        timestamp: new Date().toISOString()
      }
      messages.value.push(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearMessages = () => {
    messages.value = []
    currentConversation.value = null
  }

  const updateSettings = (newSettings) => {
    settings.value = { ...settings.value, ...newSettings }
  }

  return {
    messages,
    currentConversation,
    loading,
    streaming,
    error,
    settings,
    messageCount,
    hasMessages,
    sendMessage,
    clearMessages,
    updateSettings
  }
})
