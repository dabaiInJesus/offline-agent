<template>
  <div class="space-y-6">
    <!-- 欢迎区域 -->
    <div class="card p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">
            欢迎使用 Offline Agent
          </h2>
          <p class="text-gray-600 dark:text-gray-400">
            基于 LangChain 和 LangGraph 的本地 AI 智能体平台
          </p>
        </div>
        <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900/30 rounded-2xl flex items-center justify-center">
          <svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        v-for="stat in stats"
        :key="stat.name"
        :title="stat.name"
        :value="stat.value"
        :icon="stat.icon"
        :color="stat.color"
        :trend="stat.trend"
      />
    </div>

    <!-- 功能区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 快速操作 -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">快速操作</h3>
        <div class="grid grid-cols-2 gap-4">
          <QuickAction
            v-for="action in quickActions"
            :key="action.name"
            :name="action.name"
            :description="action.description"
            :icon="action.icon"
            :to="action.to"
            :color="action.color"
          />
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="card p-6">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4">系统状态</h3>
        <div class="space-y-4">
          <StatusItem
            v-for="item in statusItems"
            :key="item.name"
            :name="item.name"
            :status="item.status"
            :detail="item.detail"
          />
        </div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="card p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-800 dark:text-white">最近活动</h3>
        <button class="text-primary-600 hover:text-primary-700 text-sm font-medium">
          查看全部
        </button>
      </div>
      <div class="space-y-3">
        <ActivityItem
          v-for="(activity, index) in recentActivities"
          :key="index"
          :type="activity.type"
          :title="activity.title"
          :time="activity.time"
          :description="activity.description"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatCard from '../components/dashboard/StatCard.vue'
import QuickAction from '../components/dashboard/QuickAction.vue'
import StatusItem from '../components/dashboard/StatusItem.vue'
import ActivityItem from '../components/dashboard/ActivityItem.vue'
import {
  ChatBubbleLeftRightIcon,
  CircleStackIcon,
  BookOpenIcon,
  CpuChipIcon,
  BoltIcon,
  CodeBracketIcon,
  WrenchIcon,
  CommandLineIcon
} from '@heroicons/vue/24/outline'

const stats = ref([
  { name: '对话次数', value: '128', icon: ChatBubbleLeftRightIcon, color: 'blue', trend: '+12%' },
  { name: '数据库连接', value: '4', icon: CircleStackIcon, color: 'green', trend: '稳定' },
  { name: '知识库', value: '3', icon: BookOpenIcon, color: 'purple', trend: '+1' },
  { name: 'Agent 运行', value: '5', icon: CpuChipIcon, color: 'yellow', trend: '活跃' }
])

const quickActions = ref([
  { name: '开始对话', description: '与 AI 智能体对话', icon: BoltIcon, to: '/chat', color: 'blue' },
  { name: '查询数据库', description: '执行 SQL 查询', icon: CodeBracketIcon, to: '/database', color: 'green' },
  { name: '搜索知识库', description: '检索文档信息', icon: BookOpenIcon, to: '/knowledge-base', color: 'purple' },
  { name: '执行技能', description: '运行预设技能', icon: WrenchIcon, to: '/skills', color: 'yellow' }
])

const statusItems = ref([
  { name: 'Ollama 服务', status: 'online', detail: 'qwen2.5:14b' },
  { name: '数据库连接', status: 'online', detail: 'MySQL, PostgreSQL' },
  { name: '向量数据库', status: 'online', detail: 'ChromaDB' },
  { name: 'MCP 服务', status: 'offline', detail: '未启动' }
])

const recentActivities = ref([
  { type: 'chat', title: '执行了数据分析对话', time: '5 分钟前', description: '使用 Agent 分析销售数据' },
  { type: 'database', title: '执行 SQL 查询', time: '15 分钟前', description: 'SELECT * FROM users LIMIT 10' },
  { type: 'kb', title: '查询知识库', time: '30 分钟前', description: '搜索产品文档相关信息' },
  { type: 'skill', title: '执行数据导出技能', time: '1 小时前', description: '导出用户数据到 CSV' }
])
</script>
