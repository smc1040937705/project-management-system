import apiClient from './client'
import type { Task, TaskCreate, TaskUpdate, TaskDependencyCreate } from '@/types'

export const tasksApi = {
  getTasks: (params?: { skip?: number; limit?: number; project_id?: number; status?: string; priority?: string; assignee_id?: number; search?: string }) =>
    apiClient.get<Task[]>('/tasks', { params }),

  getTask: (id: number) =>
    apiClient.get<Task>(`/tasks/${id}`),

  createTask: (data: TaskCreate) =>
    apiClient.post<Task>('/tasks', data),

  updateTask: (id: number, data: TaskUpdate) =>
    apiClient.put<Task>(`/tasks/${id}`, data),

  deleteTask: (id: number) =>
    apiClient.delete(`/tasks/${id}`),

  addDependency: (taskId: number, data: TaskDependencyCreate) =>
    apiClient.post(`/tasks/${taskId}/dependencies`, data),

  removeDependency: (taskId: number, dependencyId: number) =>
    apiClient.delete(`/tasks/${taskId}/dependencies/${dependencyId}`)
}
