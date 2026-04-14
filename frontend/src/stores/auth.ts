import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserLogin, UserCreate } from '@/types'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'))

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isProjectManager = computed(() => 
    user.value?.role === 'admin' || user.value?.role === 'project_manager'
  )

  const setAuthData = (authToken: string, refToken: string, userData: User) => {
    token.value = authToken
    refreshToken.value = refToken
    user.value = userData
    localStorage.setItem('token', authToken)
    localStorage.setItem('refreshToken', refToken)
  }

  const clearAuthData = () => {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
  }

  const login = async (credentials: UserLogin) => {
    const response = await authApi.login(credentials)
    const { access_token, refresh_token } = response.data
    
    // 先保存 token，这样 getMe 才能带上认证头
    localStorage.setItem('token', access_token)
    localStorage.setItem('refreshToken', refresh_token)
    
    const userResponse = await authApi.getMe()
    setAuthData(access_token, refresh_token, userResponse.data)
    
    return userResponse.data
  }

  const register = async (data: UserCreate) => {
    const response = await authApi.register(data)
    return response.data
  }

  const logout = () => {
    clearAuthData()
  }

  const fetchUser = async () => {
    if (!token.value) return null
    
    try {
      const response = await authApi.getMe()
      user.value = response.data
      return response.data
    } catch {
      clearAuthData()
      return null
    }
  }

  const init = async () => {
    if (token.value) {
      await fetchUser()
    }
  }

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    isAdmin,
    isProjectManager,
    login,
    register,
    logout,
    fetchUser,
    init
  }
})
