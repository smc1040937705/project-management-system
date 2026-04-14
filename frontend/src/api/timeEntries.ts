import apiClient from './client'
import type { TimeEntry, TimeEntryCreate, TimeEntryUpdate } from '@/types'

export const timeEntriesApi = {
  getTimeEntries: (params?: { skip?: number; limit?: number; task_id?: number; user_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get<TimeEntry[]>('/time-entries', { params }),

  getTimeEntry: (id: number) =>
    apiClient.get<TimeEntry>(`/time-entries/${id}`),

  createTimeEntry: (data: TimeEntryCreate) =>
    apiClient.post<TimeEntry>('/time-entries', data),

  updateTimeEntry: (id: number, data: TimeEntryUpdate) =>
    apiClient.put<TimeEntry>(`/time-entries/${id}`, data),

  deleteTimeEntry: (id: number) =>
    apiClient.delete(`/time-entries/${id}`),

  getSummary: (params?: { user_id?: number; project_id?: number; start_date?: string; end_date?: string }) =>
    apiClient.get('/time-entries/summary', { params })
}
