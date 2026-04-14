import { describe, it, expect, beforeEach, vi } from 'vitest'
import { tasksApi } from '../tasks'
import apiClient from '../client'

vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Tasks API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getTasks 应发送正确的 GET 请求', async () => {
    const mockResponse = {
      data: [
        { id: 1, title: 'Task 1' },
        { id: 2, title: 'Task 2' }
      ]
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await tasksApi.getTasks()

    expect(apiClient.get).toHaveBeenCalledWith('/tasks', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  it('getTasks 应带过滤参数发送请求', async () => {
    const params = {
      skip: 0,
      limit: 10,
      project_id: 1,
      status: 'in_progress',
      priority: 'high',
      assignee_id: 1,
      search: 'bug'
    }

    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    await tasksApi.getTasks(params)

    expect(apiClient.get).toHaveBeenCalledWith('/tasks', { params })
  })

  it('getTask 应发送正确的 GET 请求', async () => {
    const taskId = 1
    const mockResponse = {
      data: { id: 1, title: 'Test Task', status: 'todo' }
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await tasksApi.getTask(taskId)

    expect(apiClient.get).toHaveBeenCalledWith(`/tasks/${taskId}`)
    expect(result).toEqual(mockResponse)
  })

  it('createTask 应发送正确的 POST 请求', async () => {
    const taskData = {
      title: 'New Task',
      description: 'Task Description',
      status: 'todo',
      priority: 'medium',
      project_id: 1,
      assignee_id: 1
    }

    const mockResponse = {
      data: { id: 1, ...taskData }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await tasksApi.createTask(taskData)

    expect(apiClient.post).toHaveBeenCalledWith('/tasks', taskData)
    expect(result).toEqual(mockResponse)
  })

  it('updateTask 应发送正确的 PUT 请求', async () => {
    const taskId = 1
    const updateData = {
      title: 'Updated Task',
      status: 'done',
      priority: 'low'
    }

    const mockResponse = {
      data: { id: 1, ...updateData }
    }

    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const result = await tasksApi.updateTask(taskId, updateData)

    expect(apiClient.put).toHaveBeenCalledWith(`/tasks/${taskId}`, updateData)
    expect(result).toEqual(mockResponse)
  })

  it('deleteTask 应发送正确的 DELETE 请求', async () => {
    const taskId = 1

    vi.mocked(apiClient.delete).mockResolvedValue({ status: 204 })

    const result = await tasksApi.deleteTask(taskId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/tasks/${taskId}`)
    expect(result).toEqual({ status: 204 })
  })

  it('addDependency 应发送正确的 POST 请求', async () => {
    const taskId = 1
    const dependencyData = {
      depends_on_task_id: 2,
      dependency_type: 'finish_to_start'
    }

    const mockResponse = {
      data: { id: 1, task_id: 1, depends_on_task_id: 2 }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await tasksApi.addDependency(taskId, dependencyData)

    expect(apiClient.post).toHaveBeenCalledWith(`/tasks/${taskId}/dependencies`, dependencyData)
    expect(result).toEqual(mockResponse)
  })

  it('removeDependency 应发送正确的 DELETE 请求', async () => {
    const taskId = 1
    const dependencyId = 1

    vi.mocked(apiClient.delete).mockResolvedValue({ status: 204 })

    const result = await tasksApi.removeDependency(taskId, dependencyId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/tasks/${taskId}/dependencies/${dependencyId}`)
    expect(result).toEqual({ status: 204 })
  })

  it('getTask 任务不存在时应抛出异常', async () => {
    const mockError = new Error('Task not found')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(tasksApi.getTask(999)).rejects.toThrow('Task not found')
  })

  it('createTask 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      tasksApi.createTask({ title: 'Test', project_id: 1, status: 'todo' } as any)
    ).rejects.toThrow('Not enough permissions')
  })

  it('updateTask 参数校验失败应抛出异常', async () => {
    const mockError = new Error('Title is required')
    vi.mocked(apiClient.put).mockRejectedValue(mockError)

    await expect(
      tasksApi.updateTask(1, { title: '' } as any)
    ).rejects.toThrow('Title is required')
  })

  it('deleteTask 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.delete).mockRejectedValue(mockError)

    await expect(tasksApi.deleteTask(1)).rejects.toThrow('Not enough permissions')
  })

  it('addDependency 循环依赖应抛出异常', async () => {
    const mockError = new Error('Circular dependency detected')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      tasksApi.addDependency(1, { depends_on_task_id: 1 })
    ).rejects.toThrow('Circular dependency detected')
  })

  it('getTasks 网络错误应抛出异常', async () => {
    const mockError = new Error('Network Error')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(tasksApi.getTasks()).rejects.toThrow('Network Error')
  })

  it('getTasks 应处理空列表返回', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await tasksApi.getTasks()

    expect(result.data).toHaveLength(0)
  })
})
