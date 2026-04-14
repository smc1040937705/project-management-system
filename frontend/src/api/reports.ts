import apiClient from './client'
import type { ProjectStatistics, UserStatistics } from '@/types'

export const reportsApi = {
  getProjectStatistics: () =>
    apiClient.get<ProjectStatistics>('/reports/projects/statistics'),

  getSingleProjectStatistics: (projectId: number) =>
    apiClient.get(`/reports/projects/${projectId}/statistics`),

  getUsersStatistics: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<UserStatistics[]>('/reports/users/statistics', { params }),

  getUserStatistics: (userId: number) =>
    apiClient.get<UserStatistics>(`/reports/users/${userId}/statistics`),

  getTimeReport: (params?: { start_date?: string; end_date?: string; project_id?: number; user_id?: number; group_by?: string }) =>
    apiClient.get('/reports/time/summary', { params })
}
