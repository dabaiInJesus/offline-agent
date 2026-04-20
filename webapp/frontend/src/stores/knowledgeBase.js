import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useKnowledgeBaseStore = defineStore('knowledgeBase', () => {
  // State
  const knowledgeBases = ref([])
  const currentKB = ref(null)
  const queryResult = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const kbList = computed(() => knowledgeBases.value)
  const hasKnowledgeBases = computed(() => knowledgeBases.value.length > 0)

  // Actions
  const fetchKnowledgeBases = async () => {
    loading.value = true
    try {
      const response = await axios.get('/api/knowledge-bases')
      knowledgeBases.value = response.data.knowledge_bases || []
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const selectKB = (kbName) => {
    currentKB.value = kbName
  }

  const queryKnowledgeBase = async (query) => {
    if (!currentKB.value) {
      error.value = '请先选择知识库'
      return
    }

    loading.value = true
    try {
      const response = await axios.post('/api/knowledge-base/query', {
        kb_name: currentKB.value,
        query: query
      })
      queryResult.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const addDocument = async (filePath) => {
    if (!currentKB.value) {
      error.value = '请先选择知识库'
      return
    }

    loading.value = true
    try {
      const response = await axios.post(`/api/knowledge-base/${currentKB.value}/documents`, {
        file_path: filePath
      })
      await fetchKnowledgeBases() // 刷新列表
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearQueryResult = () => {
    queryResult.value = null
  }

  return {
    knowledgeBases,
    currentKB,
    queryResult,
    loading,
    error,
    kbList,
    hasKnowledgeBases,
    fetchKnowledgeBases,
    selectKB,
    queryKnowledgeBase,
    addDocument,
    clearQueryResult
  }
})
