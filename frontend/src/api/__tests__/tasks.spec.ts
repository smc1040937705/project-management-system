import { describe, it, expect, vi, beforeEach } from 'vitest'
import { tasksApi } from '../tasks'
import apiClient from '../client'
import type { TaskCreate, TaskUpdate, TaskDependencyCreate } from '@/types'

// Mock apiClient
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Tasks API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * 测试场景：正常获取任务列表
   * 验证：GET请求被正确发送到/tasks
   */
  it('should call getTasks endpoint', async () => {
    const mockResponse = {
      data: [
        {
          id: 1,
          project_id: 1,
          title: 'Task 1',
          status: 'todo',
          priority: 'high',
          created_by: 1,
          actual_hours: 0,
          created_at: '2024-01-01T00:00:00Z',
          subtasks: [],
          dependencies: []
        }
      ]
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await tasksApi.getTasks()

    expect(apiClient.get).toHaveBeenCalledWith('/tasks', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：带参数获取任务列表
   * 验证：查询参数被正确传递
   */
  it('should call getTasks with query params', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const params = {
      project_id: 1,
      status: 'in_progress',
      priority: 'high',
      assignee_id: 1,
      search: 'test'
    }

    await tasksApi.getTasks(params)

    expect(apiClient.get).toHaveBeenCalledWith('/tasks', { params })
  })

  /**
   * 测试场景：获取任务列表失败
   * 验证：错误被正确抛出
   */
  it('should throw error when getTasks fails', async () => {
    const error = new Error('Network error')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(tasksApi.getTasks()).rejects.toThrow('Network error')
  })

  /**
   * 测试场景：正常获取单个任务
   * 验证：GET请求被正确发送到/tasks/{id}
   */
  it('should call getTask endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        project_id: 1,
        title: 'Task 1',
        status: 'todo',
        priority: 'high',
        created_by: 1,
        actual_hours: 0,
        created_at: '2024-01-01T00:00:00Z',
        subtasks: [],
        dependencies: []
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await tasksApi.getTask(1)

    expect(apiClient.get).toHaveBeenCalledWith('/tasks/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：获取不存在的任务
   * 验证：错误被正确抛出
   */
  it('should throw error when task not found', async () => {
    const error = new Error('Task not found')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(tasksApi.getTask(999)).rejects.toThrow('Task not found')
  })

  /**
   * 测试场景：正常创建任务
   * 验证：POST请求被正确发送到/tasks
   */
  it('should call createTask endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        project_id: 1,
        title: 'New Task',
        status: 'todo',
        priority: 'medium',
        created_by: 1,
        actual_hours: 0,
        created_at: '2024-01-01T00:00:00Z',
        subtasks: [],
        dependencies: []
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const taskData: TaskCreate = {
      project_id: 1,
      title: 'New Task',
      description: 'Description',
      status: 'todo',
      priority: 'medium',
      assignee_id: 1
    }

    const result = await tasksApi.createTask(taskData)

    expect(apiClient.post).toHaveBeenCalledWith('/tasks', taskData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：创建任务失败（项目不存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when createTask project not found', async () => {
    const error = new Error('Project not found')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const taskData: TaskCreate = {
      project_id: 999,
      title: 'New Task',
      status: 'todo',
      priority: 'medium'
    }

    await expect(tasksApi.createTask(taskData)).rejects.toThrow('Project not found')
  })

  /**
   * 测试场景：正常更新任务
   * 验证：PUT请求被正确发送到/tasks/{id}
   */
  it('should call updateTask endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        project_id: 1,
        title: 'Updated Task',
        status: 'in_progress',
        priority: 'high',
        created_by: 1,
        actual_hours: 5,
        created_at: '2024-01-01T00:00:00Z',
        subtasks: [],
        dependencies: []
      }
    }
    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const updateData: TaskUpdate = {
      title: 'Updated Task',
      status: 'in_progress'
    }

    const result = await tasksApi.updateTask(1, updateData)

    expect(apiClient.put).toHaveBeenCalledWith('/tasks/1', updateData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：更新任务失败（权限不足）
   * 验证：错误被正确抛出
   */
  it('should throw error when updateTask permission denied', async () => {
    const error = new Error('Permission denied')
    vi.mocked(apiClient.put).mockRejectedValue(error)

    await expect(tasksApi.updateTask(1, { title: 'New' })).rejects.toThrow('Permission denied')
  })

  /**
   * 测试场景：正常删除任务
   * 验证：DELETE请求被正确发送到/tasks/{id}
   */
  it('should call deleteTask endpoint', async () => {
    const mockResponse = { data: undefined }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await tasksApi.deleteTask(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/tasks/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：删除任务失败
   * 验证：错误被正确抛出
   */
  it('should throw error when deleteTask fails', async () => {
    const error = new Error('Task not found')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(tasksApi.deleteTask(999)).rejects.toThrow('Task not found')
  })

  /**
   * 测试场景：正常添加任务依赖
   * 验证：POST请求被正确发送
   */
  it('should call addDependency endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        task_id: 1,
        depends_on_task_id: 2,
        dependency_type: 'finish_to_start',
        created_at: '2024-01-01T00:00:00Z'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const depData: TaskDependencyCreate = {
      depends_on_task_id: 2,
      dependency_type: 'finish_to_start'
    }

    const result = await tasksApi.addDependency(1, depData)

    expect(apiClient.post).toHaveBeenCalledWith('/tasks/1/dependencies', depData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：添加依赖失败（循环依赖）
   * 验证：错误被正确抛出
   */
  it('should throw error when addDependency creates circular dependency', async () => {
    const error = new Error('Circular dependency detected')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const depData: TaskDependencyCreate = {
      depends_on_task_id: 2
    }

    await expect(tasksApi.addDependency(1, depData)).rejects.toThrow('Circular dependency detected')
  })

  /**
   * 测试场景：正常移除任务依赖
   * 验证：DELETE请求被正确发送
   */
  it('should call removeDependency endpoint', async () => {
    const mockResponse = { data: undefined }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await tasksApi.removeDependency(1, 2)

    expect(apiClient.delete).toHaveBeenCalledWith('/tasks/1/dependencies/2')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：移除依赖失败
   * 验证：错误被正确抛出
   */
  it('should throw error when removeDependency fails', async () => {
    const error = new Error('Dependency not found')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(tasksApi.removeDependency(1, 999)).rejects.toThrow('Dependency not found')
  })
})
