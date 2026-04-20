<template>
  <div class="space-y-6">
    <div class="card p-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">知识库管理</h2>

      <!-- 知识库列表 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800 dark:text-white">知识库列表</h3>
          <button @click="kbStore.fetchKnowledgeBases" class="btn-secondary" :disabled="kbStore.loading">
            刷新
          </button>
        </div>

        <div v-if="kbStore.loading" class="text-center py-8 text-gray-500">
          <div class="loading-spinner mx-auto mb-2"></div>
          加载中...
        </div>

        <div v-else-if="!kbStore.hasKnowledgeBases" class="text-center py-8 text-gray-500">
          <BookOpenIcon class="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>暂无知识库</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="kb in kbStore.kbList"
            :key="kb.name"
            class="p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 cursor-pointer transition-colors"
            :class="{ 'border-primary-500 bg-primary-50 dark:bg-primary-900/20': kbStore.currentKB === kb.name }"
            @click="kbStore.selectKB(kb.name)"
          >
            <div class="flex items-center space-x-3 mb-2">
              <BookOpenIcon class="w-5 h-5 text-purple-600" />
              <h4 class="font-medium text-gray-800 dark:text-white">{{ kb.name }}</h4>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              文档数: {{ kb.document_count || 0 }}
            </p>
          </div>
        </div>
      </div>

      <!-- 查询 -->
      <div v-if="kbStore.currentKB" class="mb-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">查询知识库: {{ kbStore.currentKB }}</h3>
        <div class="space-y-3">
          <textarea
            v-model="queryText"
            class="textarea"
            rows="3"
            placeholder="输入查询问题..."
          ></textarea>
          <button
            @click="queryKB"
            class="btn-primary"
            :disabled="!queryText.trim() || kbStore.loading"
          >
            <span v-if="kbStore.loading" class="loading-spinner mr-2"></span>
            查询
          </button>
        </div>
      </div>

      <!-- 查询结果 -->
      <div v-if="kbStore.queryResult" class="mt-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">查询结果</h3>
        <div class="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <p class="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{{ kbStore.queryResult.answer || JSON.stringify(kbStore.queryResult, null, 2) }}</p>
          <div v-if="kbStore.queryResult.sources" class="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <p class="text-sm text-gray-500 mb-2">来源:</p>
            <div v-for="(source, index) in kbStore.queryResult.sources" :key="index" class="text-sm text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded mb-1">
              {{ source.metadata?.source || '未知来源' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="kbStore.error" class="mt-4 p-4 bg-red-100 dark:bg-red-900/30 rounded-lg text-red-700 dark:text-red-300 text-sm">
        {{ kbStore.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useKnowledgeBaseStore } from '../stores/knowledgeBase'
import { BookOpenIcon } from '@heroicons/vue/24/outline'

const kbStore = useKnowledgeBaseStore()
const queryText = ref('')

const queryKB = async () => {
  if (!queryText.value.trim()) return
  try {
    await kbStore.queryKnowledgeBase(queryText.value)
  } catch (error) {
    console.error('查询失败:', error)
  }
}

onMounted(() => {
  kbStore.fetchKnowledgeBases()
})
</script>
