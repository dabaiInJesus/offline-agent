<template>
  <div class="h-[calc(100vh-8rem)] flex flex-col">
    <!-- 设置栏 -->
    <div class="card p-4 mb-4">
      <div class="flex items-center space-x-4 flex-wrap gap-y-2">
        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Agent 类型:</label>
          <select v-model="chatStore.settings.agentType" class="select w-32">
            <option value="">普通对话</option>
            <option value="react">ReAct</option>
            <option value="tool">Tool</option>
            <option value="graph">Graph</option>
          </select>
        </div>

        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">知识库:</label>
          <select v-model="chatStore.settings.useKnowledgeBase" class="select w-40">
            <option :value="null">不使用</option>
            <option v-for="kb in kbStore.kbList" :key="kb.name" :value="kb.name">
              {{ kb.name }}
            </option>
          </select>
        </div>

        <div class="flex items-center space-x-2">
          <label class="text-sm font-medium text-gray-700 dark:text-gray-300">数据库:</label>
          <select v-model="chatStore.settings.useDatabase" class="select w-40">
            <option :value="null">不使用</option>
            <option v-for="db in dbStore.databaseList" :key="db" :value="db">
              {{ db }}
            </option>
          </select>
        </div>

        <button 
          @click="chatStore.clearMessages"
          class="btn-secondary ml-auto"
          :disabled="!chatStore.hasMessages"
        >
          清空对话
        </button>
      </div>
    </div>

    <!-- 消息区域 -->
    <div class="flex-1 card overflow-hidden flex flex-col">
      <div 
        ref="messageContainer"
        class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin"
      >
        <!-- 欢迎消息 -->
        <div v-if="!chatStore.hasMessages" class="text-center py-12">
          <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <ChatBubbleLeftRightIcon class="w-8 h-8 text-primary-600" />
          </div>
          <h3 class="text-lg font-medium text-gray-800 dark:text-white mb-2">开始对话</h3>
          <p class="text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            你可以直接输入问题，或选择上方的 Agent 类型、知识库、数据库来增强对话能力
          </p>
        </div>

        <!-- 消息列表 -->
        <ChatMessage
          v-for="message in chatStore.messages"
          :key="message.id"
          :message="message"
        />

        <!-- 加载状态 -->
        <div v-if="chatStore.loading" class="flex items-center space-x-2 text-gray-500">
          <div class="loading-spinner"></div>
          <span>思考中...</span>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-4">
        <div class="flex items-end space-x-2">
          <textarea
            v-model="inputMessage"
            @keydown.enter.prevent="sendMessage"
            placeholder="输入消息..."
            class="textarea flex-1 min-h-[80px] max-h-[200px]"
            :disabled="chatStore.loading"
          ></textarea>
          <button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || chatStore.loading"
            class="btn-primary h-10 px-4"
          >
            <PaperAirplaneIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useChatStore } from '../stores/chat'
import { useDatabaseStore } from '../stores/database'
import { useKnowledgeBaseStore } from '../stores/knowledgeBase'
import ChatMessage from '../components/chat/ChatMessage.vue'
import { ChatBubbleLeftRightIcon, PaperAirplaneIcon } from '@heroicons/vue/24/outline'

const chatStore = useChatStore()
const dbStore = useDatabaseStore()
const kbStore = useKnowledgeBaseStore()

const inputMessage = ref('')
const messageContainer = ref(null)

const sendMessage = async () => {
  if (!inputMessage.value.trim() || chatStore.loading) return

  const message = inputMessage.value
  inputMessage.value = ''

  try {
    await chatStore.sendMessage(message)
    scrollToBottom()
  } catch (error) {
    console.error('发送失败:', error)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, scrollToBottom)

onMounted(() => {
  dbStore.fetchDatabases()
  kbStore.fetchKnowledgeBases()
})
</script>
