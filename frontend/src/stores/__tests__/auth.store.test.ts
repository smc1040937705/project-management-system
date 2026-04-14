import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import { authApi } from '@/api'

vi.mock('@/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    refreshToken: vi.fn()
  }
}))

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  role: 'member',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z'
}

const mockToken = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer'
}

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('初始化时用户和token应为空', () => {
    const store = useAuthStore()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('isAdmin 应在用户角色为 admin 时返回 true', () => {
    const store = useAuthStore()
    store.user = { ...mockUser, role: 'admin' }
    store.token = 'test-token'
    expect(store.isAdmin).toBe(true)
    expect(store.isAuthenticated).toBe(true)
  })

  it('isProjectManager 应在管理员或项目经理时返回 true', () => {
    const store = useAuthStore()
    
    store.user = { ...mockUser, role: 'admin' }
    expect(store.isProjectManager).toBe(true)
    
    store.user = { ...mockUser, role: 'project_manager' }
    expect(store.isProjectManager).toBe(true)
    
    store.user = { ...mockUser, role: 'member' }
    expect(store.isProjectManager).toBe(false)
  })

  it('登录成功后应设置认证数据', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ data: mockToken } as any)
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)

    const store = useAuthStore()
    const result = await store.login({ username: 'testuser', password: 'password123' })

    expect(authApi.login).toHaveBeenCalledWith({ username: 'testuser', password: 'password123' })
    expect(authApi.getMe).toHaveBeenCalled()
    expect(result).toEqual(mockUser)
    expect(store.user).toEqual(mockUser)
    expect(store.token).toBe(mockToken.access_token)
    expect(store.refreshToken).toBe(mockToken.refresh_token)
    expect(localStorage.getItem('token')).toBe(mockToken.access_token)
    expect(localStorage.getItem('refreshToken')).toBe(mockToken.refresh_token)
  })

  it('登录失败应抛出异常', async () => {
    const mockError = new Error('Invalid credentials')
    vi.mocked(authApi.login).mockRejectedValue(mockError)

    const store = useAuthStore()
    
    await expect(
      store.login({ username: 'wrong', password: 'wrong' })
    ).rejects.toThrow('Invalid credentials')
    
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })

  it('注册应调用 API 并返回数据', async () => {
    const registerData = {
      username: 'newuser',
      email: 'new@example.com',
      password: 'password123',
      first_name: 'New',
      last_name: 'User',
      role: 'member'
    }
    
    vi.mocked(authApi.register).mockResolvedValue({ data: mockUser } as any)

    const store = useAuthStore()
    const result = await store.register(registerData)

    expect(authApi.register).toHaveBeenCalledWith(registerData)
    expect(result).toEqual(mockUser)
  })

  it('注册失败应抛出异常', async () => {
    const mockError = new Error('Email already exists')
    vi.mocked(authApi.register).mockRejectedValue(mockError)

    const store = useAuthStore()
    
    await expect(
      store.register({
        username: 'existing',
        email: 'existing@example.com',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
        role: 'member'
      })
    ).rejects.toThrow('Email already exists')
  })

  it('登出应清除所有认证数据', () => {
    const store = useAuthStore()
    store.user = mockUser
    store.token = mockToken.access_token
    store.refreshToken = mockToken.refresh_token
    localStorage.setItem('token', mockToken.access_token)
    localStorage.setItem('refreshToken', mockToken.refresh_token)

    store.logout()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
  })

  it('fetchUser 在有 token 时应获取用户信息', async () => {
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)

    const store = useAuthStore()
    store.token = mockToken.access_token

    const result = await store.fetchUser()

    expect(authApi.getMe).toHaveBeenCalled()
    expect(result).toEqual(mockUser)
    expect(store.user).toEqual(mockUser)
  })

  it('fetchUser 在没有 token 时应返回 null', async () => {
    const store = useAuthStore()
    store.token = null

    const result = await store.fetchUser()

    expect(authApi.getMe).not.toHaveBeenCalled()
    expect(result).toBeNull()
  })

  it('fetchUser 失败时应清除认证数据', async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error('Token expired'))

    const store = useAuthStore()
    store.token = 'expired-token'

    const result = await store.fetchUser()

    expect(result).toBeNull()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('init 在有 token 时应调用 fetchUser', async () => {
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)

    const store = useAuthStore()
    store.token = mockToken.access_token
    
    await store.init()

    expect(authApi.getMe).toHaveBeenCalled()
    expect(store.user).toEqual(mockUser)
  })

  it('init 在没有 token 时不调用 fetchUser', async () => {
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)

    const store = useAuthStore()
    store.token = null
    
    await store.init()

    expect(authApi.getMe).not.toHaveBeenCalled()
  })

  it('setAuthData 应正确设置所有状态', () => {
    const store = useAuthStore()
    
    store.setAuthData(mockToken.access_token, mockToken.refresh_token, mockUser)

    expect(store.token).toBe(mockToken.access_token)
    expect(store.refreshToken).toBe(mockToken.refresh_token)
    expect(store.user).toEqual(mockUser)
    expect(localStorage.getItem('token')).toBe(mockToken.access_token)
    expect(localStorage.getItem('refreshToken')).toBe(mockToken.refresh_token)
  })

  it('clearAuthData 应清除所有状态', () => {
    const store = useAuthStore()
    store.token = mockToken.access_token
    store.refreshToken = mockToken.refresh_token
    store.user = mockUser

    store.clearAuthData()

    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(localStorage.getItem('refreshToken')).toBeNull()
  })

  it('登录时网络错误应抛出异常并保持未认证状态', async () => {
    const mockError = new Error('Network Error')
    vi.mocked(authApi.login).mockRejectedValue(mockError)

    const store = useAuthStore()
    
    await expect(
      store.login({ username: 'testuser', password: 'password123' })
    ).rejects.toThrow('Network Error')
    
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('登录成功但获取用户信息失败应清除认证数据', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ data: mockToken } as any)
    vi.mocked(authApi.getMe).mockRejectedValue(new Error('Failed to get user info'))

    const store = useAuthStore()
    
    await expect(
      store.login({ username: 'testuser', password: 'password123' })
    ).rejects.toThrow('Failed to get user info')
    
    expect(store.user).toBeNull()
  })

  it('refreshToken 失败应抛出异常', async () => {
    const mockError = new Error('Invalid refresh token')
    vi.mocked(authApi.refreshToken).mockRejectedValue(mockError)

    const store = useAuthStore()
    
    await expect(
      authApi.refreshToken('invalid-token')
    ).rejects.toThrow('Invalid refresh token')
  })

  it('空状态下 isAuthenticated 应为 false', () => {
    const store = useAuthStore()
    
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.isProjectManager).toBe(false)
  })

  it('只有 token 没有用户数据时 isAuthenticated 应为 false', () => {
    const store = useAuthStore()
    store.token = mockToken.access_token
    store.user = null
    
    expect(store.isAuthenticated).toBe(false)
  })

  it('只有用户数据没有 token 时 isAuthenticated 应为 false', () => {
    const store = useAuthStore()
    store.token = null
    store.user = mockUser
    
    expect(store.isAuthenticated).toBe(false)
  })

  it('注册时网络错误应抛出异常', async () => {
    const mockError = new Error('Network Error')
    vi.mocked(authApi.register).mockRejectedValue(mockError)

    const store = useAuthStore()
    
    await expect(
      store.register({
        username: 'test',
        email: 'test@example.com',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
        role: 'member'
      })
    ).rejects.toThrow('Network Error')
  })

  it('init 在没有 token 时不调用 fetchUser', async () => {
    const store = useAuthStore()
    store.token = null
    
    const fetchUserSpy = vi.spyOn(store, 'fetchUser')
    
    await store.init()

    expect(fetchUserSpy).not.toHaveBeenCalled()
  })

  it('isProjectManager 对 team_lead 角色应返回 false', () => {
    const store = useAuthStore()
    store.user = { ...mockUser, role: 'team_lead' }
    store.token = mockToken.access_token
    
    expect(store.isProjectManager).toBe(false)
  })

  it('重复登出不会产生副作用', () => {
    const store = useAuthStore()
    store.user = mockUser
    store.token = mockToken.access_token

    store.logout()
    store.logout()
    store.logout()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
  })
})
