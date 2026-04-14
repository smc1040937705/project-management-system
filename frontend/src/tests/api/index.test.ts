import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
    },
  }
})

describe('apiClient', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  it('应创建带有正确配置的axios实例', () => {
    expect(axios.create).toHaveBeenCalled()
  })
})

describe('authApi', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  describe('login', () => {
    it('应发送登录请求', async () => {
      const mockResponse = {
        access_token: 'test-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer',
      }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { authApi } = await import('@/api')
      const result = await authApi.login({ username: 'test', password: 'password' })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/login', {
        username: 'test',
        password: 'password',
      })
    })
  })

  describe('register', () => {
    it('应发送注册请求', async () => {
      const mockResponse = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { authApi } = await import('@/api')
      const result = await authApi.register({
        email: 'test@example.com',
        username: 'testuser',
        password: 'password123',
        first_name: 'Test',
        last_name: 'User',
        role: 'member',
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/register', expect.any(Object))
    })
  })

  describe('getMe', () => {
    it('应获取当前用户信息', async () => {
      const mockResponse = {
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        first_name: 'Test',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      }
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { authApi } = await import('@/api')
      const result = await authApi.getMe()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/auth/me')
    })
  })

  describe('refreshToken', () => {
    it('应刷新token', async () => {
      const mockResponse = {
        access_token: 'new-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer',
      }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { authApi } = await import('@/api')
      const result = await authApi.refreshToken('old-refresh-token')

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'old-refresh-token',
      })
    })
  })
})

describe('projectsApi', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  describe('getProjects', () => {
    it('应获取项目列表', async () => {
      const mockResponse = [
        { id: 1, name: 'Project 1', status: 'active' },
        { id: 2, name: 'Project 2', status: 'planning' },
      ]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      const result = await projectsApi.getProjects()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/projects', { params: undefined })
    })

    it('应带参数获取项目列表', async () => {
      const mockResponse = [{ id: 1, name: 'Project 1', status: 'active' }]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      const params = { status: 'active', search: 'test' }
      await projectsApi.getProjects(params)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/projects', { params })
    })
  })

  describe('getProject', () => {
    it('应获取单个项目', async () => {
      const mockResponse = { id: 1, name: 'Project 1', status: 'active' }
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      const result = await projectsApi.getProject(1)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/projects/1')
    })
  })

  describe('createProject', () => {
    it('应创建项目', async () => {
      const mockResponse = { id: 1, name: 'New Project', status: 'planning' }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      const result = await projectsApi.createProject({
        name: 'New Project',
        status: 'planning',
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/projects', {
        name: 'New Project',
        status: 'planning',
      })
    })
  })

  describe('updateProject', () => {
    it('应更新项目', async () => {
      const mockResponse = { id: 1, name: 'Updated Project', status: 'active' }
      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      const result = await projectsApi.updateProject(1, { name: 'Updated Project' })

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/projects/1', { name: 'Updated Project' })
    })
  })

  describe('deleteProject', () => {
    it('应删除项目', async () => {
      mockAxiosInstance.delete.mockResolvedValue({})

      const { projectsApi } = await import('@/api')
      await projectsApi.deleteProject(1)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/projects/1')
    })
  })

  describe('addMember', () => {
    it('应添加项目成员', async () => {
      const mockResponse = { id: 1, members: [{ id: 2 }] }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      await projectsApi.addMember(1, 2)

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/projects/1/members/2')
    })
  })

  describe('removeMember', () => {
    it('应移除项目成员', async () => {
      const mockResponse = { id: 1, members: [] }
      mockAxiosInstance.delete.mockResolvedValue({ data: mockResponse })

      const { projectsApi } = await import('@/api')
      await projectsApi.removeMember(1, 2)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/projects/1/members/2')
    })
  })
})

describe('tasksApi', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  describe('getTasks', () => {
    it('应获取任务列表', async () => {
      const mockResponse = [
        { id: 1, title: 'Task 1', status: 'todo' },
        { id: 2, title: 'Task 2', status: 'in_progress' },
      ]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      await tasksApi.getTasks()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tasks', { params: undefined })
    })

    it('应带参数获取任务列表', async () => {
      const mockResponse = [{ id: 1, title: 'Task 1', status: 'todo' }]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      const params = { project_id: 1, status: 'todo', priority: 'high' }
      await tasksApi.getTasks(params)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tasks', { params })
    })
  })

  describe('getTask', () => {
    it('应获取单个任务', async () => {
      const mockResponse = { id: 1, title: 'Task 1', status: 'todo' }
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      await tasksApi.getTask(1)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/tasks/1')
    })
  })

  describe('createTask', () => {
    it('应创建任务', async () => {
      const mockResponse = { id: 1, title: 'New Task', status: 'todo' }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      await tasksApi.createTask({
        project_id: 1,
        title: 'New Task',
        status: 'todo',
        priority: 'medium',
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/tasks', expect.any(Object))
    })
  })

  describe('updateTask', () => {
    it('应更新任务', async () => {
      const mockResponse = { id: 1, title: 'Updated Task', status: 'done' }
      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      await tasksApi.updateTask(1, { status: 'done' })

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/tasks/1', { status: 'done' })
    })
  })

  describe('deleteTask', () => {
    it('应删除任务', async () => {
      mockAxiosInstance.delete.mockResolvedValue({})

      const { tasksApi } = await import('@/api')
      await tasksApi.deleteTask(1)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/tasks/1')
    })
  })

  describe('addDependency', () => {
    it('应添加任务依赖', async () => {
      const mockResponse = { id: 1, task_id: 1, depends_on_task_id: 2 }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { tasksApi } = await import('@/api')
      await tasksApi.addDependency(1, { depends_on_task_id: 2 })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/tasks/1/dependencies', { depends_on_task_id: 2 })
    })
  })

  describe('removeDependency', () => {
    it('应移除任务依赖', async () => {
      mockAxiosInstance.delete.mockResolvedValue({})

      const { tasksApi } = await import('@/api')
      await tasksApi.removeDependency(1, 1)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/tasks/1/dependencies/1')
    })
  })
})

describe('timeEntriesApi', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  describe('getTimeEntries', () => {
    it('应获取工时记录列表', async () => {
      const mockResponse = [
        { id: 1, task_id: 1, hours: 2 },
        { id: 2, task_id: 1, hours: 3 },
      ]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { timeEntriesApi } = await import('@/api')
      await timeEntriesApi.getTimeEntries()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/time-entries', { params: undefined })
    })
  })

  describe('createTimeEntry', () => {
    it('应创建工时记录', async () => {
      const mockResponse = { id: 1, task_id: 1, hours: 2, description: 'Work' }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { timeEntriesApi } = await import('@/api')
      await timeEntriesApi.createTimeEntry({
        task_id: 1,
        hours: 2,
        date: '2024-01-01',
      })

      expect(mockAxiosInstance.post).toHaveBeenCalledWith('/time-entries', expect.any(Object))
    })
  })

  describe('updateTimeEntry', () => {
    it('应更新工时记录', async () => {
      const mockResponse = { id: 1, hours: 3 }
      mockAxiosInstance.put.mockResolvedValue({ data: mockResponse })

      const { timeEntriesApi } = await import('@/api')
      await timeEntriesApi.updateTimeEntry(1, { hours: 3 })

      expect(mockAxiosInstance.put).toHaveBeenCalledWith('/time-entries/1', { hours: 3 })
    })
  })

  describe('deleteTimeEntry', () => {
    it('应删除工时记录', async () => {
      mockAxiosInstance.delete.mockResolvedValue({})

      const { timeEntriesApi } = await import('@/api')
      await timeEntriesApi.deleteTimeEntry(1)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/time-entries/1')
    })
  })

  describe('getSummary', () => {
    it('应获取工时汇总', async () => {
      const mockResponse = { total_hours: 10, daily_breakdown: [] }
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { timeEntriesApi } = await import('@/api')
      await timeEntriesApi.getSummary({ user_id: 1 })

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/time-entries/summary', { params: { user_id: 1 } })
    })
  })
})

describe('documentsApi', () => {
  let mockAxiosInstance: any

  beforeEach(async () => {
    vi.clearAllMocks()
    mockAxiosInstance = axios.create()
  })

  describe('getDocuments', () => {
    it('应获取文档列表', async () => {
      const mockResponse = [
        { id: 1, name: 'Document 1' },
        { id: 2, name: 'Document 2' },
      ]
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { documentsApi } = await import('@/api')
      await documentsApi.getDocuments()

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/documents', { params: undefined })
    })
  })

  describe('getDocument', () => {
    it('应获取单个文档', async () => {
      const mockResponse = { id: 1, name: 'Document 1' }
      mockAxiosInstance.get.mockResolvedValue({ data: mockResponse })

      const { documentsApi } = await import('@/api')
      await documentsApi.getDocument(1)

      expect(mockAxiosInstance.get).toHaveBeenCalledWith('/documents/1')
    })
  })

  describe('uploadDocument', () => {
    it('应上传文档', async () => {
      const mockResponse = { id: 1, name: 'test.pdf', file_path: '/uploads/test.pdf' }
      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse })

      const { documentsApi } = await import('@/api')
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })
      await documentsApi.uploadDocument(1, file, 'Test Document', 'Test description')

      expect(mockAxiosInstance.post).toHaveBeenCalled()
    })
  })

  describe('deleteDocument', () => {
    it('应删除文档', async () => {
      mockAxiosInstance.delete.mockResolvedValue({})

      const { documentsApi } = await import('@/api')
      await documentsApi.deleteDocument(1)

      expect(mockAxiosInstance.delete).toHaveBeenCalledWith('/documents/1')
    })
  })
})
