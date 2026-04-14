import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, UserCreate, UserUpdate } from '@/types'
import { usersApi } from '@/api'

export const useUsersStore = defineStore('users', () => {
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchUsers = async (params?: { skip?: number; limit?: number; role?: string; is_active?: boolean; search?: string }) => {
    loading.value = true
    error.value = null
    try {
      const response = await usersApi.getUsers(params)
      users.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchUser = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await usersApi.getUser(id)
      currentUser.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createUser = async (data: UserCreate) => {
    loading.value = true
    error.value = null
    try {
      const response = await usersApi.createUser(data)
      users.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateUser = async (id: number, data: UserUpdate) => {
    loading.value = true
    error.value = null
    try {
      const response = await usersApi.updateUser(id, data)
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = response.data
      }
      if (currentUser.value?.id === id) {
        currentUser.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteUser = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await usersApi.deleteUser(id)
      users.value = users.value.filter(u => u.id !== id)
      if (currentUser.value?.id === id) {
        currentUser.value = null
      }
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    users,
    currentUser,
    loading,
    error,
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser
  }
})
