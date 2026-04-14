import apiClient from './client'
import type { Project, ProjectCreate, ProjectUpdate, PaginatedResponse } from '@/types'

export const projectsApi = {
  getProjects: (params?: { skip?: number; limit?: number; status?: string; search?: string }) =>
    apiClient.get<Project[]>('/projects', { params }),

  getProject: (id: number) =>
    apiClient.get<Project>(`/projects/${id}`),

  createProject: (data: ProjectCreate) =>
    apiClient.post<Project>('/projects', data),

  updateProject: (id: number, data: ProjectUpdate) =>
    apiClient.put<Project>(`/projects/${id}`, data),

  deleteProject: (id: number) =>
    apiClient.delete(`/projects/${id}`),

  addMember: (projectId: number, userId: number) =>
    apiClient.post<Project>(`/projects/${projectId}/members/${userId}`),

  removeMember: (projectId: number, userId: number) =>
    apiClient.delete<Project>(`/projects/${projectId}/members/${userId}`)
}
