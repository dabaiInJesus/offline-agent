<template>
  <div class="space-y-6">
    <div class="card p-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">智能体管理</h2>

      <!-- 创建 Agent -->
      <div class="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">创建新 Agent</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Agent 名称</label>
            <input v-model="newAgent.name" type="text" class="input" placeholder="输入 Agent 名称" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Agent 类型</label>
            <select v-model="newAgent.agentType" class="select">
              <option value="react">ReAct Agent</option>
              <option value="tool">Tool Agent</option>
              <option value="graph">Graph Agent</option>
            </select>
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">系统提示词 (可选)</label>
            <textarea v-model="newAgent.systemPrompt" class="textarea" rows="2" placeholder="自定义系统提示词..."></textarea>
          </div>
        </div>
        <button @click="createAgent" class="btn-primary mt-3" :disabled="!newAgent.name.trim() || creating">
          <span v-if="creating" class="loading-spinner mr-2"></span>
          创建 Agent
        </button>
      </div>

      <!-- Agent 列表 -->
      <div>
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">Agent 列表</h3>
        <div v-if="agents.length === 0" class="text-center py-8 text-gray-500">
          <CpuChipIcon class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>暂无 Agent</p>
          <p class="text-sm mt-1">创建一个新 Agent 开始使用</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="agent in agents"
            :key="agent.name"
            class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-colors"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <CpuChipIcon class="w-5 h-5 text-primary-600" />
                <div>
                  <h4 class="font-medium text-gray-800 dark:text-white">{{ agent.name }}</h4>
                  <p class="text-sm text-gray-500 dark:text-gray-400">类型: {{ agent.agentType }}</p>
                </div>
              </div>
              <div class="flex items-center space-x-2">
                <span v-if="agent.tools && agent.tools.length > 0" class="text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-2 py-1 rounded">
                  {{ agent.tools.length }} 工具
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息 -->
      <div v-if="message" class="mt-4 p-4 rounded-lg text-sm" :class="messageType === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { CpuChipIcon } from '@heroicons/vue/24/outline'

const agents = ref([])
const newAgent = ref({
  name: '',
  agentType: 'react',
  systemPrompt: ''
})
const creating = ref(false)
const message = ref('')
const messageType = ref('success')

const createAgent = async () => {
  if (!newAgent.value.name.trim()) return
  creating.value = true
  message.value = ''
  try {
    const response = await axios.post('/api/agent/create', {
      name: newAgent.value.name,
      agent_type: newAgent.value.agentType,
      system_prompt: newAgent.value.systemPrompt || null
    })
    agents.value.push({
      name: response.data.agent_name,
      agentType: response.data.agent_type,
      tools: response.data.tools || []
    })
    message.value = `Agent "${response.data.agent_name}" 创建成功！`
    messageType.value = 'success'
    newAgent.value = { name: '', agentType: 'react', systemPrompt: '' }
  } catch (error) {
    message.value = error.response?.data?.detail || '创建 Agent 失败'
    messageType.value = 'error'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/agents/types')
    // Load agent types info
  } catch (error) {
    console.error('加载 Agent 类型失败:', error)
  }
})
</script>
