import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useDatabaseStore = defineStore('database', () => {
  // State
  const databases = ref([])
  const currentDatabase = ref(null)
  const tables = ref([])
  const currentTable = ref(null)
  const tableSchema = ref(null)
  const queryResult = ref(null)
  const queryHistory = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const databaseList = computed(() => databases.value)
  const hasDatabases = computed(() => databases.value.length > 0)

  // Actions
  const fetchDatabases = async () => {
    loading.value = true
    try {
      const response = await axios.get('/api/databases')
      databases.value = response.data.databases || []
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const selectDatabase = async (dbName) => {
    currentDatabase.value = dbName
    tables.value = []
    currentTable.value = null
    tableSchema.value = null

    try {
      const response = await axios.get(`/api/database/${dbName}/tables`)
      tables.value = response.data.tables || []
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const fetchTableSchema = async (tableName) => {
    if (!currentDatabase.value) return

    loading.value = true
    try {
      const response = await axios.get(`/api/database/${currentDatabase.value}/schema/${tableName}`)
      currentTable.value = tableName
      tableSchema.value = response.data.schema
      return response.data
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const executeQuery = async (sql) => {
    if (!currentDatabase.value) {
      error.value = '请先选择数据库'
      return
    }

    loading.value = true
    try {
      const response = await axios.post('/api/database/query', {
        db_name: currentDatabase.value,
        sql: sql
      })
      queryResult.value = response.data
      
      // 添加到历史
      queryHistory.value.unshift({
        sql: sql,
        timestamp: new Date().toISOString(),
        count: response.data.count
      })

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
    databases,
    currentDatabase,
    tables,
    currentTable,
    tableSchema,
    queryResult,
    queryHistory,
    loading,
    error,
    databaseList,
    hasDatabases,
    fetchDatabases,
    selectDatabase,
    fetchTableSchema,
    executeQuery,
    clearQueryResult
  }
})
