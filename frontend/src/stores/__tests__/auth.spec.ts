import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../auth'
import type { User, UserLogin, UserCreate } from '@/types'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock API模块
vi.mock('@/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn()
  }
}))

import { authApi } from '@/api'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  /**
   * 测试场景：store初始化
   * 验证：初始状态正确，未认证
   */
  it('should initialize with default state', () => {
    const store = useAuthStore()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.isProjectManager).toBe(false)
  })

  /**
   * 测试场景：从localStorage恢复token
   * 验证：store能正确读取已保存的token
   */
  it('should restore token from localStorage on init', () => {
    localStorageMock.getItem.mockImplementation((key: string) => {
      if (key === 'token') return 'stored-token'
      if (key === 'refreshToken') return 'stored-refresh-token'
      return null
    })

    const store = useAuthStore()

    expect(store.token).toBe('stored-token')
    expect(store.refreshToken).toBe('stored-refresh-token')
  })

  /**
   * 测试场景：正常登录成功
   * 验证：登录后状态更新，用户信息保存
   */
  it('should login successfully and update state', async () => {
    const mockUser: User = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    }

    const mockTokenResponse = {
      data: {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer'
      }
    }

    vi.mocked(authApi.login).mockResolvedValue(mockTokenResponse)
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser })

    const store = useAuthStore()
    const credentials: UserLogin = { username: 'testuser', password: 'password123' }

    const result = await store.login(credentials)

    expect(authApi.login).toHaveBeenCalledWith(credentials)
    expect(authApi.getMe).toHaveBeenCalled()
    expect(result).toEqual(mockUser)
    expect(store.user).toEqual(mockUser)
    expect(store.token).toBe('test-access-token')
    expect(store.refreshToken).toBe('test-refresh-token')
    expect(store.isAuthenticated).toBe(true)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('token', 'test-access-token')
    expect(localStorageMock.setItem).toHaveBeenCalledWith('refreshToken', 'test-refresh-token')
  })

  /**
   * 测试场景：登录失败
   * 验证：登录失败时抛出错误，状态不变
   */
  it('should throw error when login fails', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid credentials'))

    const store = useAuthStore()
    const credentials: UserLogin = { username: 'testuser', password: 'wrongpassword' }

    await expect(store.login(credentials)).rejects.toThrow('Invalid credentials')
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
  })

  /**
   * 测试场景：正常注册成功
   * 验证：注册API被正确调用
   */
  it('should register successfully', async () => {
    const mockUser: User = {
      id: 2,
      email: 'new@example.com',
      username: 'newuser',
      first_name: 'New',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    }

    vi.mocked(authApi.register).mockResolvedValue({ data: mockUser })

    const store = useAuthStore()
    const userData: UserCreate = {
      email: 'new@example.com',
      username: 'newuser',
      password: 'password123',
      first_name: 'New',
      last_name: 'User',
      role: 'member'
    }

    const result = await store.register(userData)

    expect(authApi.register).toHaveBeenCalledWith(userData)
    expect(result).toEqual(mockUser)
  })

  /**
   * 测试场景：注册失败（用户已存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when registration fails', async () => {
    vi.mocked(authApi.register).mockRejectedValue(new Error('User already exists'))

    const store = useAuthStore()
    const userData: UserCreate = {
      email: 'existing@example.com',
      username: 'existing',
      password: 'password123',
      first_name: 'Existing',
      last_name: 'User',
      role: 'member'
    }

    await expect(store.register(userData)).rejects.toThrow('User already exists')
  })

  /**
   * 测试场景：正常登出
   * 验证：状态被清空，localStorage被清理
   */
  it('should logout and clear state', () => {
    const store = useAuthStore()

    // 先设置一些状态
    store.user = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    } as User
    store.token = 'test-token'
    store.refreshToken = 'test-refresh-token'

    store.logout()

    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.isAuthenticated).toBe(false)
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('refreshToken')
  })

  /**
   * 测试场景：获取当前用户信息成功
   * 验证：用户信息被正确更新
   */
  it('should fetch user successfully', async () => {
    const mockUser: User = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    }

    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser })

    const store = useAuthStore()
    store.token = 'valid-token'

    const result = await store.fetchUser()

    expect(authApi.getMe).toHaveBeenCalled()
    expect(result).toEqual(mockUser)
    expect(store.user).toEqual(mockUser)
  })

  /**
   * 测试场景：获取用户信息失败（token无效）
   * 验证：状态被清空
   */
  it('should clear state when fetch user fails', async () => {
    vi.mocked(authApi.getMe).mockRejectedValue(new Error('Unauthorized'))

    const store = useAuthStore()
    store.token = 'invalid-token'
    store.user = { id: 1 } as User

    const result = await store.fetchUser()

    expect(result).toBeNull()
    expect(store.user).toBeNull()
    expect(store.token).toBeNull()
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('token')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('refreshToken')
  })

  /**
   * 测试场景：无token时获取用户信息
   * 验证：直接返回null，不调用API
   */
  it('should return null when fetching user without token', async () => {
    const store = useAuthStore()
    store.token = null

    const result = await store.fetchUser()

    expect(result).toBeNull()
    expect(authApi.getMe).not.toHaveBeenCalled()
  })

  /**
   * 测试场景：初始化时恢复用户会话
   * 验证：有token时自动获取用户信息
   */
  it('should init and fetch user when token exists', async () => {
    const mockUser: User = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      first_name: 'Test',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    }

    localStorageMock.getItem.mockReturnValue('stored-token')
    vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser })

    const store = useAuthStore()
    await store.init()

    expect(authApi.getMe).toHaveBeenCalled()
    expect(store.user).toEqual(mockUser)
  })

  /**
   * 测试场景：初始化时无token
   * 验证：不调用API
   */
  it('should not fetch user on init when no token', async () => {
    localStorageMock.getItem.mockReturnValue(null)

    const store = useAuthStore()
    await store.init()

    expect(authApi.getMe).not.toHaveBeenCalled()
    expect(store.user).toBeNull()
  })

  /**
   * 测试场景：管理员角色检查
   * 验证：isAdmin计算属性正确
   */
  it('should correctly identify admin user', () => {
    const store = useAuthStore()

    store.user = { role: 'admin' } as User
    expect(store.isAdmin).toBe(true)
    expect(store.isProjectManager).toBe(true)

    store.user = { role: 'project_manager' } as User
    expect(store.isAdmin).toBe(false)
    expect(store.isProjectManager).toBe(true)

    store.user = { role: 'member' } as User
    expect(store.isAdmin).toBe(false)
    expect(store.isProjectManager).toBe(false)
  })
})
