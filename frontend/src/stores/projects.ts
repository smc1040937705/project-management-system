import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types'
import { projectsApi } from '@/api'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const fetchProjects = async (params?: { skip?: number; limit?: number; status?: string; search?: string }) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.getProjects(params)
      projects.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchProject = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.getProject(id)
      currentProject.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createProject = async (data: ProjectCreate) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.createProject(data)
      projects.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateProject = async (id: number, data: ProjectUpdate) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.updateProject(id, data)
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = response.data
      }
      if (currentProject.value?.id === id) {
        currentProject.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteProject = async (id: number) => {
    loading.value = true
    error.value = null
    try {
      await projectsApi.deleteProject(id)
      projects.value = projects.value.filter(p => p.id !== id)
      if (currentProject.value?.id === id) {
        currentProject.value = null
      }
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const addMember = async (projectId: number, userId: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.addMember(projectId, userId)
      if (currentProject.value?.id === projectId) {
        currentProject.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const removeMember = async (projectId: number, userId: number) => {
    loading.value = true
    error.value = null
    try {
      const response = await projectsApi.removeMember(projectId, userId)
      if (currentProject.value?.id === projectId) {
        currentProject.value = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    projects,
    currentProject,
    loading,
    error,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    addMember,
    removeMember
  }
})
