import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import type { User, UserLogin, UserCreate } from '@/types'

const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  first_name: 'Test',
  last_name: 'User',
  role: 'member',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockAdminUser: User = {
  id: 2,
  email: 'admin@example.com',
  username: 'adminuser',
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockProjectManagerUser: User = {
  id: 3,
  email: 'pm@example.com',
  username: 'pmuser',
  first_name: 'Project',
  last_name: 'Manager',
  role: 'project_manager',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

vi.mock('@/api', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getMe: vi.fn(),
    refreshToken: vi.fn(),
  },
}))

import { authApi } from '@/api'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('初始状态', () => {
    it('初始状态应该是未认证状态', () => {
      const store = useAuthStore()
      
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
      expect(store.isAdmin).toBe(false)
      expect(store.isProjectManager).toBe(false)
    })
  })

  describe('login', () => {
    it('登录成功后应正确设置用户信息和token', async () => {
      const store = useAuthStore()
      const credentials: UserLogin = {
        username: 'testuser',
        password: 'password123',
      }

      vi.mocked(authApi.login).mockResolvedValue({
        data: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
        },
      } as any)

      vi.mocked(authApi.getMe).mockResolvedValue({
        data: mockUser,
      } as any)

      const result = await store.login(credentials)

      expect(authApi.login).toHaveBeenCalledWith(credentials)
      expect(authApi.getMe).toHaveBeenCalled()
      expect(store.user).toEqual(mockUser)
      expect(store.token).toBe('mock-access-token')
      expect(store.refreshToken).toBe('mock-refresh-token')
      expect(store.isAuthenticated).toBe(true)
      expect(result).toEqual(mockUser)
    })

    it('登录失败时应抛出错误', async () => {
      const store = useAuthStore()
      const credentials: UserLogin = {
        username: 'testuser',
        password: 'wrongpassword',
      }

      const error = new Error('Invalid credentials')
      vi.mocked(authApi.login).mockRejectedValue(error)

      await expect(store.login(credentials)).rejects.toThrow('Invalid credentials')
      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('register', () => {
    it('注册成功后应返回用户信息', async () => {
      const store = useAuthStore()
      const userData: UserCreate = {
        email: 'newuser@example.com',
        username: 'newuser',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
        role: 'member',
      }

      vi.mocked(authApi.register).mockResolvedValue({
        data: { ...mockUser, id: 4, email: userData.email, username: userData.username },
      } as any)

      const result = await store.register(userData)

      expect(authApi.register).toHaveBeenCalledWith(userData)
      expect(result.email).toBe(userData.email)
      expect(result.username).toBe(userData.username)
    })

    it('注册失败（用户名已存在）时应抛出错误', async () => {
      const store = useAuthStore()
      const userData: UserCreate = {
        email: 'existing@example.com',
        username: 'existinguser',
        password: 'password123',
        first_name: 'Existing',
        last_name: 'User',
        role: 'member',
      }

      const error = new Error('Username already exists')
      vi.mocked(authApi.register).mockRejectedValue(error)

      await expect(store.register(userData)).rejects.toThrow('Username already exists')
    })
  })

  describe('logout', () => {
    it('登出后应清除所有认证数据', async () => {
      const store = useAuthStore()
      
      vi.mocked(authApi.login).mockResolvedValue({
        data: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
        },
      } as any)
      vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)

      await store.login({ username: 'testuser', password: 'password123' })
      
      expect(store.isAuthenticated).toBe(true)

      store.logout()

      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.refreshToken).toBeNull()
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('fetchUser', () => {
    it('有token时获取用户信息成功', async () => {
      const store = useAuthStore()
      
      vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)
      
      store.token = 'existing-token'
      const result = await store.fetchUser()

      expect(authApi.getMe).toHaveBeenCalled()
      expect(store.user).toEqual(mockUser)
      expect(result).toEqual(mockUser)
    })

    it('无token时返回null', async () => {
      const store = useAuthStore()
      
      store.token = null
      const result = await store.fetchUser()

      expect(authApi.getMe).not.toHaveBeenCalled()
      expect(result).toBeNull()
    })

    it('获取用户信息失败时清除认证数据', async () => {
      const store = useAuthStore()
      
      vi.mocked(authApi.getMe).mockRejectedValue(new Error('Unauthorized'))
      
      store.token = 'invalid-token'
      const result = await store.fetchUser()

      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(result).toBeNull()
    })
  })

  describe('computed properties', () => {
    it('isAdmin 应正确判断管理员角色', () => {
      const store = useAuthStore()
      
      store.user = mockAdminUser
      store.token = 'token'
      expect(store.isAdmin).toBe(true)
      expect(store.isProjectManager).toBe(true)

      store.user = mockUser
      expect(store.isAdmin).toBe(false)
      expect(store.isProjectManager).toBe(false)
    })

    it('isProjectManager 应正确判断项目管理员角色', () => {
      const store = useAuthStore()
      
      store.user = mockProjectManagerUser
      store.token = 'token'
      expect(store.isAdmin).toBe(false)
      expect(store.isProjectManager).toBe(true)
    })

    it('isAuthenticated 需要同时有token和user', () => {
      const store = useAuthStore()
      
      store.token = 'token'
      store.user = null
      expect(store.isAuthenticated).toBe(false)

      store.token = null
      store.user = mockUser
      expect(store.isAuthenticated).toBe(false)

      store.token = 'token'
      store.user = mockUser
      expect(store.isAuthenticated).toBe(true)
    })
  })

  describe('init', () => {
    it('有token时初始化应获取用户信息', async () => {
      const store = useAuthStore()
      
      vi.mocked(authApi.getMe).mockResolvedValue({ data: mockUser } as any)
      
      store.token = 'existing-token'
      await store.init()

      expect(authApi.getMe).toHaveBeenCalled()
      expect(store.user).toEqual(mockUser)
    })

    it('无token时初始化不应获取用户信息', async () => {
      const store = useAuthStore()
      
      store.token = null
      await store.init()

      expect(authApi.getMe).not.toHaveBeenCalled()
    })
  })
})
