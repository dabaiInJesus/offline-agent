<template>
  <div class="space-y-6">
    <div class="card p-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">数据库管理</h2>

      <!-- 选择数据库 -->
      <div class="flex items-center space-x-4 mb-6">
        <select v-model="dbStore.currentDatabase" @change="onDatabaseChange" class="select flex-1">
          <option :value="null">请选择数据库</option>
          <option v-for="db in dbStore.databaseList" :key="db" :value="db">{{ db }}</option>
        </select>
        <button @click="dbStore.fetchDatabases" class="btn-secondary" :disabled="dbStore.loading">
          刷新
        </button>
      </div>

      <!-- 表列表 -->
      <div v-if="dbStore.tables.length > 0" class="mb-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">数据表</h3>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <button
            v-for="table in dbStore.tables"
            :key="table"
            @click="dbStore.fetchTableSchema(table)"
            class="p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 text-left transition-colors"
            :class="{ 'border-primary-500 bg-primary-50 dark:bg-primary-900/20': dbStore.currentTable === table }"
          >
            <div class="flex items-center space-x-2">
              <CircleStackIcon class="w-4 h-4 text-gray-400" />
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ table }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- SQL 查询 -->
      <div class="mb-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">SQL 查询</h3>
        <div class="space-y-3">
          <textarea
            v-model="sqlQuery"
            class="textarea font-mono text-sm"
            rows="4"
            placeholder="输入 SQL 查询语句..."
            :disabled="!dbStore.currentDatabase"
          ></textarea>
          <div class="flex items-center space-x-2">
            <button
              @click="executeQuery"
              class="btn-primary"
              :disabled="!sqlQuery.trim() || !dbStore.currentDatabase || dbStore.loading"
            >
              <span v-if="dbStore.loading" class="loading-spinner mr-2"></span>
              执行查询
            </button>
            <button @click="sqlQuery = ''" class="btn-secondary">清空</button>
          </div>
        </div>
      </div>

      <!-- 查询结果 -->
      <div v-if="dbStore.queryResult" class="overflow-x-auto">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-3">查询结果 ({{ dbStore.queryResult.count }} 行)</h3>
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th v-for="key in resultColumns" :key="key" class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">{{ key }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
            <tr v-for="(row, index) in resultRows" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-800">
              <td v-for="key in resultColumns" :key="key" class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">{{ row[key] }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 错误提示 -->
      <div v-if="dbStore.error" class="mt-4 p-4 bg-red-100 dark:bg-red-900/30 rounded-lg text-red-700 dark:text-red-300 text-sm">
        {{ dbStore.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDatabaseStore } from '../stores/database'
import { CircleStackIcon } from '@heroicons/vue/24/outline'

const dbStore = useDatabaseStore()
const sqlQuery = ref('')

const resultColumns = computed(() => {
  if (!dbStore.queryResult?.data?.length) return []
  return Object.keys(dbStore.queryResult.data[0])
})

const resultRows = computed(() => {
  return dbStore.queryResult?.data || []
})

const onDatabaseChange = () => {
  if (dbStore.currentDatabase) {
    dbStore.selectDatabase(dbStore.currentDatabase)
  }
}

const executeQuery = async () => {
  if (!sqlQuery.value.trim()) return
  try {
    await dbStore.executeQuery(sqlQuery.value)
  } catch (error) {
    console.error('查询失败:', error)
  }
}

onMounted(() => {
  dbStore.fetchDatabases()
})
</script>
