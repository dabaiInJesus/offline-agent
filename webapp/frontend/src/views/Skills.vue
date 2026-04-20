<template>
  <div class="space-y-6">
    <div class="card p-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">技能中心</h2>

      <!-- 技能列表 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-white">可用技能</h3>
          <button @click="fetchSkills" class="btn-secondary" :disabled="loading">
            刷新
          </button>
        </div>

        <div v-if="loading" class="text-center py-8 text-gray-500">
          <div class="loading-spinner mx-auto mb-2"></div>
          加载中...
        </div>

        <div v-else-if="skills.length === 0" class="text-center py-8 text-gray-500">
          <WrenchScrewdriverIcon class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>暂无技能</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="skill in skills"
            :key="skill.name"
            class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 transition-colors"
          >
            <div class="flex items-center space-x-3 mb-2">
              <WrenchScrewdriverIcon class="w-5 h-5 text-yellow-600" />
              <h4 class="font-medium text-gray-800 dark:text-white">{{ skill.name }}</h4>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">{{ skill.description || '无描述' }}</p>
            <button
              @click="selectSkill(skill)"
              class="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              执行
            </button>
          </div>
        </div>
      </div>

      <!-- 执行技能 -->
      <div v-if="selectedSkill" class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">执行技能: {{ selectedSkill.name }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">{{ selectedSkill.description }}</p>
        <div class="space-y-3">
          <textarea
            v-model="skillParams"
            class="textarea font-mono text-sm"
            rows="4"
            placeholder='输入参数 (JSON 格式)，例如: {"query": "hello"}'
          ></textarea>
          <div class="flex items-center space-x-2">
            <button
              @click="executeSkill"
              class="btn-primary"
              :disabled="executing"
            >
              <span v-if="executing" class="loading-spinner mr-2"></span>
              执行
            </button>
            <button @click="selectedSkill = null" class="btn-secondary">取消</button>
          </div>
        </div>
      </div>

      <!-- 执行结果 -->
      <div v-if="skillResult" class="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">执行结果</h3>
        <div v-if="skillResult.success" class="text-green-600 dark:text-green-400 text-sm mb-2">执行成功</div>
        <div v-else class="text-red-600 dark:text-red-400 text-sm mb-2">执行失败: {{ skillResult.error }}</div>
        <div v-if="skillResult.message" class="text-sm text-gray-600 dark:text-gray-400 mb-2">{{ skillResult.message }}</div>
        <pre v-if="skillResult.data" class="text-sm text-gray-800 dark:text-gray-200 overflow-auto max-h-60 bg-white dark:bg-gray-900 p-3 rounded">{{ JSON.stringify(skillResult.data, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { WrenchScrewdriverIcon } from '@heroicons/vue/24/outline'

const skills = ref([])
const loading = ref(false)
const selectedSkill = ref(null)
const skillParams = ref('{}')
const executing = ref(false)
const skillResult = ref(null)

const fetchSkills = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/skills')
    skills.value = response.data.skills || []
  } catch (error) {
    console.error('获取技能列表失败:', error)
  } finally {
    loading.value = false
  }
}

const selectSkill = (skill) => {
  selectedSkill.value = skill
  skillResult.value = null
  skillParams.value = '{}'
}

const executeSkill = async () => {
  if (!selectedSkill.value) return
  executing.value = true
  skillResult.value = null
  try {
    let params = {}
    try {
      params = JSON.parse(skillParams.value)
    } catch {
      params = { input: skillParams.value }
    }
    const response = await axios.post('/api/skill/execute', {
      skill_name: selectedSkill.value.name,
      parameters: params
    })
    skillResult.value = response.data
  } catch (error) {
    skillResult.value = {
      success: false,
      error: error.response?.data?.detail || error.message
    }
  } finally {
    executing.value = false
  }
}

onMounted(() => {
  fetchSkills()
})
</script>
