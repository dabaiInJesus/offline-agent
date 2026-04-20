import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAppStore = defineStore('app', () => {
  // State
  const status = ref({
    initialized: false,
    timestamp: null
  })
  const loading = ref(false)
  const darkMode = ref(localStorage.getItem('darkMode') === 'true')
  const sidebarCollapsed = ref(false)

  // Getters
  const isInitialized = computed(() => status.value.initialized)
  const isDarkMode = computed(() => darkMode.value)

  // Actions
  const fetchStatus = async () => {
    try {
      const response = await axios.get('/api/status')
      status.value = response.data
      return response.data
    } catch (error) {
      console.error('获取状态失败:', error)
      return null
    }
  }

  const toggleDarkMode = () => {
    darkMode.value = !darkMode.value
    localStorage.setItem('darkMode', darkMode.value)
    if (darkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const initDarkMode = () => {
    if (darkMode.value) {
      document.documentElement.classList.add('dark')
    }
  }

  return {
    status,
    loading,
    darkMode,
    sidebarCollapsed,
    isInitialized,
    isDarkMode,
    fetchStatus,
    toggleDarkMode,
    toggleSidebar,
    initDarkMode
  }
})
