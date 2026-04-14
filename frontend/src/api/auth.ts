import apiClient from './client'
import type { User, UserLogin, UserCreate, Token } from '@/types'

export const authApi = {
  login: (data: UserLogin) =>
    apiClient.post<Token>('/auth/login', data),

  register: (data: UserCreate) =>
    apiClient.post<User>('/auth/register', data),

  getMe: () =>
    apiClient.get<User>('/auth/me'),

  refreshToken: (refreshToken: string) =>
    apiClient.post<Token>('/auth/refresh', { refresh_token: refreshToken })
}
