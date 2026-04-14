import { describe, it, expect, vi, beforeEach } from 'vitest'
import { authApi } from '../auth'
import apiClient from '../client'
import type { UserLogin, UserCreate } from '@/types'

// Mock apiClient
vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * 测试场景：正常登录请求
   * 验证：POST请求被正确发送到/auth/login
   */
  it('should call login endpoint with correct data', async () => {
    const mockResponse = {
      data: {
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        token_type: 'bearer'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const credentials: UserLogin = {
      username: 'testuser',
      password: 'password123'
    }

    const result = await authApi.login(credentials)

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', credentials)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：登录失败
   * 验证：错误被正确抛出
   */
  it('should throw error when login fails', async () => {
    const error = new Error('Invalid credentials')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const credentials: UserLogin = {
      username: 'testuser',
      password: 'wrongpassword'
    }

    await expect(authApi.login(credentials)).rejects.toThrow('Invalid credentials')
  })

  /**
   * 测试场景：正常注册请求
   * 验证：POST请求被正确发送到/auth/register
   */
  it('should call register endpoint with correct data', async () => {
    const mockResponse = {
      data: {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const userData: UserCreate = {
      email: 'test@example.com',
      username: 'testuser',
      password: 'password123',
      first_name: 'Test',
      last_name: 'User',
      role: 'member'
    }

    const result = await authApi.register(userData)

    expect(apiClient.post).toHaveBeenCalledWith('/auth/register', userData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：注册失败（用户已存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when registration fails', async () => {
    const error = new Error('Email already registered')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const userData: UserCreate = {
      email: 'existing@example.com',
      username: 'existing',
      password: 'password123',
      first_name: 'Existing',
      last_name: 'User',
      role: 'member'
    }

    await expect(authApi.register(userData)).rejects.toThrow('Email already registered')
  })

  /**
   * 测试场景：正常获取当前用户信息
   * 验证：GET请求被正确发送到/auth/me
   */
  it('should call getMe endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await authApi.getMe()

    expect(apiClient.get).toHaveBeenCalledWith('/auth/me')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：获取当前用户失败（未认证）
   * 验证：错误被正确抛出
   */
  it('should throw error when getMe fails', async () => {
    const error = new Error('Unauthorized')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(authApi.getMe()).rejects.toThrow('Unauthorized')
  })

  /**
   * 测试场景：正常刷新token
   * 验证：POST请求被正确发送到/auth/refresh
   */
  it('should call refreshToken endpoint', async () => {
    const mockResponse = {
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await authApi.refreshToken('old-refresh-token')

    expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', {
      refresh_token: 'old-refresh-token'
    })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：刷新token失败
   * 验证：错误被正确抛出
   */
  it('should throw error when refreshToken fails', async () => {
    const error = new Error('Invalid refresh token')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    await expect(authApi.refreshToken('invalid-token')).rejects.toThrow('Invalid refresh token')
  })
})
