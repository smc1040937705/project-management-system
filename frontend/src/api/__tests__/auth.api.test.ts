import { describe, it, expect, beforeEach, vi } from 'vitest'
import { authApi } from '../auth'
import apiClient from '../client'

vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Auth API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('login 应发送正确的 POST 请求', async () => {
    const credentials = {
      username: 'testuser',
      password: 'password123'
    }

    const mockResponse = {
      data: {
        access_token: 'test-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer'
      }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await authApi.login(credentials)

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', credentials)
    expect(result).toEqual(mockResponse)
  })

  it('register 应发送正确的 POST 请求', async () => {
    const userData = {
      username: 'newuser',
      email: 'new@example.com',
      password: 'password123',
      first_name: 'New',
      last_name: 'User',
      role: 'member'
    }

    const mockResponse = {
      data: {
        id: 1,
        username: 'newuser',
        email: 'new@example.com'
      }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await authApi.register(userData)

    expect(apiClient.post).toHaveBeenCalledWith('/auth/register', userData)
    expect(result).toEqual(mockResponse)
  })

  it('getMe 应发送正确的 GET 请求', async () => {
    const mockResponse = {
      data: {
        id: 1,
        username: 'testuser',
        email: 'test@example.com'
      }
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await authApi.getMe()

    expect(apiClient.get).toHaveBeenCalledWith('/auth/me')
    expect(result).toEqual(mockResponse)
  })

  it('refreshToken 应发送正确的 POST 请求', async () => {
    const refreshToken = 'test-refresh-token'

    const mockResponse = {
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer'
      }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await authApi.refreshToken(refreshToken)

    expect(apiClient.post).toHaveBeenCalledWith('/auth/refresh', { refresh_token: refreshToken })
    expect(result).toEqual(mockResponse)
  })

  it('login 失败时应抛出异常', async () => {
    const mockError = new Error('Invalid credentials')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      authApi.login({ username: 'wrong', password: 'wrong' })
    ).rejects.toThrow('Invalid credentials')
  })

  it('register 邮箱已存在时应抛出异常', async () => {
    const mockError = new Error('Email already registered')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      authApi.register({
        username: 'existing',
        email: 'existing@example.com',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
        role: 'member'
      })
    ).rejects.toThrow('Email already registered')
  })

  it('getMe token 无效时应抛出异常', async () => {
    const mockError = new Error('Invalid token')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(authApi.getMe()).rejects.toThrow('Invalid token')
  })
})
