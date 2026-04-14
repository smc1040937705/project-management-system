import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Task, TaskCreate, TaskUpdate, TaskDependencyCreate } from '@/types'
import { tasksApi } from '@/api'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchTasks = async (params?: { skip?: number; limit?: number; project_id?: number; status?: string; priority?: string; assignee_id?: number; search?: string }) => {
    loading.value = true
    error.value = null
    try {
      const response = await tasksApi.getTasks(params)
      tasks.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchTask = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await tasksApi.getTask(id)
      currentTask.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createTask = async (data: TaskCreate) => {
    loading.value = true
    error.value = null
    try {
      const response = await tasksApi.createTask(data)
      tasks.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTask = async (id: number, data: TaskUpdate) => {
    loading.value = true
    error.value = null
    try {
      const response = await tasksApi.updateTask(id, data)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      if (currentTask.value?.id === id) {
        currentTask.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteTask = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await tasksApi.deleteTask(id)
      tasks.value = tasks.value.filter(t => t.id !== id)
      if (currentTask.value?.id === id) {
        currentTask.value = null
      }
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const addDependency = async (taskId: number, data: TaskDependencyCreate) => {
    loading.value = true
    error.value = null
    try {
      const response = await tasksApi.addDependency(taskId, data)
      if (currentTask.value?.id === taskId) {
        currentTask.value.dependencies.push(response.data)
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const removeDependency = async (taskId: number, dependencyId: number) => {
    loading.value = true
    error.value = null
    try {
      await tasksApi.removeDependency(taskId, dependencyId)
      if (currentTask.value?.id === taskId) {
        currentTask.value.dependencies = currentTask.value.dependencies.filter(d => d.id !== dependencyId)
      }
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    tasks,
    currentTask,
    loading,
    error,
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    addDependency,
    removeDependency
  }
})
