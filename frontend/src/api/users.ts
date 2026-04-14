import apiClient from './client'
import type { User, UserCreate, UserUpdate } from '@/types'

export const usersApi = {
  getUsers: (params?: { skip?: number; limit?: number; role?: string; is_active?: boolean; search?: string }) =>
    apiClient.get<User[]>('/users', { params }),

  getUser: (id: number) =>
    apiClient.get<User>(`/users/${id}`),

  createUser: (data: UserCreate) =>
    apiClient.post<User>('/users', data),

  updateUser: (id: number, data: UserUpdate) =>
    apiClient.put<User>(`/users/${id}`, data),

  deleteUser: (id: number) =>
    apiClient.delete(`/users/${id}`)
}
