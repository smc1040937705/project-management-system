import apiClient from './client'
import type { Notification, NotificationCreate } from '@/types'

export const notificationsApi = {
  getNotifications: (params?: { skip?: number; limit?: number; is_read?: boolean; type?: string }) =>
    apiClient.get<Notification[]>('/notifications', { params }),

  getUnreadCount: () =>
    apiClient.get<{ unread_count: number }>('/notifications/unread-count'),

  getNotification: (id: number) =>
    apiClient.get<Notification>(`/notifications/${id}`),

  createNotification: (data: NotificationCreate) =>
    apiClient.post<Notification>('/notifications', data),

  markAsRead: (id: number) =>
    apiClient.put<Notification>(`/notifications/${id}/read`),

  markAllAsRead: () =>
    apiClient.put('/notifications/mark-all-read'),

  deleteNotification: (id: number) =>
    apiClient.delete(`/notifications/${id}`)
}
