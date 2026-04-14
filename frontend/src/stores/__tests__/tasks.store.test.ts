import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '../tasks'
import { tasksApi } from '@/api'

vi.mock('@/api', () => ({
  tasksApi: {
    getTasks: vi.fn(),
    getTask: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    addDependency: vi.fn(),
    removeDependency: vi.fn()
  }
}))

const mockTask = {
  id: 1,
  title: 'Test Task',
  description: 'Test Description',
  status: 'in_progress',
  priority: 'high',
  project_id: 1,
  project: { id: 1, name: 'Test Project' },
  assignee_id: 1,
  assignee: { id: 1, username: 'assignee' },
  dependencies: [],
  due_date: '2024-12-31',
  created_at: '2024-01-01T00:00:00Z'
}

const mockTasks = [
  mockTask,
  {
    id: 2,
    title: 'Second Task',
    description: 'Another task',
    status: 'pending',
    priority: 'medium',
    project_id: 1,
    assignee_id: 2,
    dependencies: [],
    created_at: '2024-01-02T00:00:00Z'
  }
]

describe('Tasks Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    const store = useTasksStore()
    store.tasks = []
    store.currentTask = null
    store.error = null
    store.loading = false
  })

  it('初始化时任务列表应为空', () => {
    const store = useTasksStore()
    expect(store.tasks).toEqual([])
    expect(store.currentTask).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchTasks 成功时应更新任务列表', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: mockTasks } as any)

    const store = useTasksStore()
    const result = await store.fetchTasks()

    expect(tasksApi.getTasks).toHaveBeenCalledWith(undefined)
    expect(store.tasks).toEqual(mockTasks)
    expect(result).toEqual(mockTasks)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchTasks 应带过滤参数', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: mockTasks } as any)

    const store = useTasksStore()
    const params = {
      skip: 0,
      limit: 10,
      project_id: 1,
      status: 'in_progress',
      priority: 'high',
      assignee_id: 1,
      search: 'Test'
    }
    
    await store.fetchTasks(params)

    expect(tasksApi.getTasks).toHaveBeenCalledWith(params)
  })

  it('fetchTasks 失败时应设置错误', async () => {
    const mockError = new Error('Failed to fetch tasks')
    vi.mocked(tasksApi.getTasks).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(store.fetchTasks()).rejects.toThrow('Failed to fetch tasks')
    
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Failed to fetch tasks')
  })

  it('fetchTask 成功时应设置 currentTask', async () => {
    vi.mocked(tasksApi.getTask).mockResolvedValue({ data: mockTask } as any)

    const store = useTasksStore()
    const result = await store.fetchTask(1)

    expect(tasksApi.getTask).toHaveBeenCalledWith(1)
    expect(store.currentTask).toEqual(mockTask)
    expect(result).toEqual(mockTask)
  })

  it('fetchTask 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(tasksApi.getTask).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(store.fetchTask(999)).rejects.toThrow('Not enough permissions')
    
    expect(store.currentTask).toBeNull()
    expect(store.error).toBe('Not enough permissions')
  })

  it('createTask 成功时应添加到任务列表', async () => {
    const newTaskData = {
      title: 'New Task',
      description: 'New Description',
      status: 'pending',
      priority: 'medium',
      project_id: 1,
      assignee_id: 1
    }

    const createdTask = { ...mockTask, id: 3, title: 'New Task' }
    vi.mocked(tasksApi.createTask).mockResolvedValue({ data: createdTask } as any)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    
    const result = await store.createTask(newTaskData)

    expect(tasksApi.createTask).toHaveBeenCalledWith(newTaskData)
    expect(store.tasks).toContainEqual(createdTask)
    expect(store.tasks.length).toBe(3)
    expect(result).toEqual(createdTask)
  })

  it('createTask 验证失败应抛出异常', async () => {
    const mockError = new Error('Title is required')
    vi.mocked(tasksApi.createTask).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.tasks = [...mockTasks]

    await expect(
      store.createTask({ title: '', description: '', status: 'pending' } as any)
    ).rejects.toThrow('Title is required')
    
    expect(store.tasks.length).toBe(2)
    expect(store.error).toBe('Title is required')
  })

  it('updateTask 成功时应更新任务列表', async () => {
    const updateData = {
      title: 'Updated Task',
      status: 'done',
      priority: 'low'
    }
    const updatedTask = { ...mockTask, ...updateData }
    
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: updatedTask } as any)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    
    const result = await store.updateTask(1, updateData)

    expect(tasksApi.updateTask).toHaveBeenCalledWith(1, updateData)
    expect(store.tasks.find(t => t.id === 1)?.title).toBe('Updated Task')
    expect(store.tasks.find(t => t.id === 1)?.status).toBe('done')
    expect(result).toEqual(updatedTask)
  })

  it('updateTask 应更新 currentTask 如果匹配', async () => {
    const updateData = { status: 'done' }
    const updatedTask = { ...mockTask, ...updateData }
    
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: updatedTask } as any)

    const store = useTasksStore()
    store.currentTask = mockTask
    
    await store.updateTask(1, updateData)

    expect(store.currentTask?.status).toBe('done')
  })

  it('deleteTask 成功时应从列表移除', async () => {
    vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined as any)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    
    await store.deleteTask(1)

    expect(tasksApi.deleteTask).toHaveBeenCalledWith(1)
    expect(store.tasks.find(t => t.id === 1)).toBeUndefined()
    expect(store.tasks.length).toBe(1)
  })

  it('deleteTask 应清空 currentTask 如果匹配', async () => {
    vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined as any)

    const store = useTasksStore()
    store.currentTask = mockTask
    
    await store.deleteTask(1)

    expect(store.currentTask).toBeNull()
  })

  it('addDependency 应更新 currentTask 的依赖列表', async () => {
    const newDependency = {
      id: 1,
      task_id: 1,
      depends_on_task_id: 2,
      created_at: '2024-01-01T00:00:00Z'
    }
    
    vi.mocked(tasksApi.addDependency).mockResolvedValue({ data: newDependency } as any)

    const store = useTasksStore()
    store.currentTask = { ...mockTask, dependencies: [] }
    
    const dependencyData = { depends_on_task_id: 2 }
    const result = await store.addDependency(1, dependencyData)

    expect(tasksApi.addDependency).toHaveBeenCalledWith(1, dependencyData)
    expect(store.currentTask?.dependencies).toContainEqual(newDependency)
    expect(result).toEqual(newDependency)
  })

  it('removeDependency 应从 currentTask 移除依赖', async () => {
    const dependencyToRemove = {
      id: 1,
      task_id: 1,
      depends_on_task_id: 2,
      created_at: '2024-01-01T00:00:00Z'
    }
    
    vi.mocked(tasksApi.removeDependency).mockResolvedValue(undefined as any)

    const store = useTasksStore()
    store.currentTask = {
      ...mockTask,
      dependencies: [dependencyToRemove]
    }
    
    await store.removeDependency(1, 1)

    expect(tasksApi.removeDependency).toHaveBeenCalledWith(1, 1)
    expect(store.currentTask?.dependencies).toHaveLength(0)
  })

  it('addDependency 失败应抛出异常', async () => {
    const mockError = new Error('Circular dependency detected')
    vi.mocked(tasksApi.addDependency).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.currentTask = { ...mockTask, dependencies: [] }

    await expect(
      store.addDependency(1, { depends_on_task_id: 1 })
    ).rejects.toThrow('Circular dependency detected')
  })

  it('操作过程中应正确维护 loading 状态', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: mockTasks } as any)
    vi.mocked(tasksApi.createTask).mockResolvedValue({ data: mockTask } as any)

    const store = useTasksStore()
    
    const fetchPromise = store.fetchTasks()
    expect(store.loading).toBe(true)
    await fetchPromise
    expect(store.loading).toBe(false)
    
    const createPromise = store.createTask({ title: 'Test' } as any)
    expect(store.loading).toBe(true)
    await createPromise
    expect(store.loading).toBe(false)
  })

  it('错误应被正确捕获并存储', async () => {
    const errors = ['Network error', 'Validation failed', 'Permission denied']
    
    for (const errorMsg of errors) {
      vi.mocked(tasksApi.getTasks).mockRejectedValueOnce(new Error(errorMsg))
      
      const store = useTasksStore()
      
      await expect(store.fetchTasks()).rejects.toThrow(errorMsg)
      expect(store.error).toBe(errorMsg)
      expect(store.loading).toBe(false)
    }
  })

  it('空状态下任务列表和当前任务应为空', () => {
    const store = useTasksStore()
    
    expect(store.tasks).toEqual([])
    expect(store.currentTask).toBeNull()
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('fetchTasks 权限不足应设置错误并保持空列表', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(tasksApi.getTasks).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(store.fetchTasks()).rejects.toThrow('Not enough permissions')
    
    expect(store.error).toBe('Not enough permissions')
    expect(store.tasks).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchTasks 参数校验失败应抛出异常', async () => {
    const mockError = new Error('Validation failed: limit must be between 1 and 100')
    vi.mocked(tasksApi.getTasks).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(
      store.fetchTasks({ limit: 999 })
    ).rejects.toThrow('Validation failed')
    
    expect(store.error).toBe('Validation failed: limit must be between 1 and 100')
  })

  it('fetchTask 任务不存在应抛出异常并保持 currentTask 为空', async () => {
    const mockError = new Error('Task not found')
    vi.mocked(tasksApi.getTask).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(store.fetchTask(999)).rejects.toThrow('Task not found')
    
    expect(store.error).toBe('Task not found')
    expect(store.currentTask).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('createTask 参数校验失败应抛出异常并保持任务列表', async () => {
    const mockError = new Error('Title is required')
    vi.mocked(tasksApi.createTask).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    const initialLength = store.tasks.length

    await expect(
      store.createTask({ title: '', project_id: 1 } as any)
    ).rejects.toThrow('Title is required')
    
    expect(store.error).toBe('Title is required')
    expect(store.tasks.length).toBe(initialLength)
    expect(store.loading).toBe(false)
  })

  it('createTask 项目不存在应抛出异常', async () => {
    const mockError = new Error('Project not found')
    vi.mocked(tasksApi.createTask).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    const initialLength = store.tasks.length

    await expect(
      store.createTask({ title: 'Test', project_id: 999, status: 'todo' } as any)
    ).rejects.toThrow('Project not found')
    
    expect(store.error).toBe('Project not found')
    expect(store.tasks.length).toBe(initialLength)
  })

  it('updateTask 权限不足应抛出异常并保持原有数据', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(tasksApi.updateTask).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    const originalTitle = store.tasks[0].title

    await expect(
      store.updateTask(1, { title: 'Hacked' })
    ).rejects.toThrow('Not enough permissions')
    
    expect(store.tasks[0].title).toBe(originalTitle)
    expect(store.error).toBe('Not enough permissions')
  })

  it('updateTask 任务不存在应抛出异常', async () => {
    const mockError = new Error('Task not found')
    vi.mocked(tasksApi.updateTask).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(
      store.updateTask(999, { status: 'done' })
    ).rejects.toThrow('Task not found')
    
    expect(store.error).toBe('Task not found')
  })

  it('deleteTask 权限不足应抛出异常并保持任务列表', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(tasksApi.deleteTask).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.tasks = [...mockTasks]
    const initialLength = store.tasks.length

    await expect(store.deleteTask(1)).rejects.toThrow('Not enough permissions')
    
    expect(store.tasks.length).toBe(initialLength)
    expect(store.error).toBe('Not enough permissions')
  })

  it('deleteTask 任务不存在应抛出异常', async () => {
    const mockError = new Error('Task not found')
    vi.mocked(tasksApi.deleteTask).mockRejectedValue(mockError)

    const store = useTasksStore()

    await expect(store.deleteTask(999)).rejects.toThrow('Task not found')
    
    expect(store.error).toBe('Task not found')
  })

  it('removeDependency 依赖不存在应抛出异常', async () => {
    const mockError = new Error('Dependency not found')
    vi.mocked(tasksApi.removeDependency).mockRejectedValue(mockError)

    const store = useTasksStore()
    store.currentTask = { ...mockTask, dependencies: [] }

    await expect(
      store.removeDependency(1, 999)
    ).rejects.toThrow('Dependency not found')
    
    expect(store.error).toBe('Dependency not found')
  })

  it('fetchTasks 返回空列表应正确处理', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: [] } as any)

    const store = useTasksStore()
    
    const result = await store.fetchTasks()

    expect(result).toEqual([])
    expect(store.tasks).toEqual([])
    expect(store.error).toBeNull()
  })

  it('非匹配 ID 的更新不影响 currentTask', async () => {
    const updateData = { status: 'done' }
    const updatedTask = { ...mockTask, id: 999, ...updateData }
    
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: updatedTask } as any)

    const store = useTasksStore()
    store.currentTask = mockTask
    
    await store.updateTask(999, updateData)

    expect(store.currentTask?.status).toBe('in_progress')
  })

  it('非匹配 ID 的删除不影响 currentTask', async () => {
    vi.mocked(tasksApi.deleteTask).mockResolvedValue(undefined as any)

    const store = useTasksStore()
    store.currentTask = mockTask
    
    await store.deleteTask(999)

    expect(store.currentTask).not.toBeNull()
  })

  it('非匹配 ID 的添加依赖不影响 currentTask', async () => {
    const newDependency = {
      id: 1,
      task_id: 999,
      depends_on_task_id: 2,
      created_at: '2024-01-01T00:00:00Z'
    }
    
    vi.mocked(tasksApi.addDependency).mockResolvedValue({ data: newDependency } as any)

    const store = useTasksStore()
    store.currentTask = { ...mockTask, dependencies: [] }
    
    await store.addDependency(999, { depends_on_task_id: 2 })

    expect(store.currentTask?.dependencies).toHaveLength(0)
  })

  it('非匹配 ID 的移除依赖不影响 currentTask', async () => {
    const dependencyToRemove = {
      id: 1,
      task_id: 999,
      depends_on_task_id: 2,
      created_at: '2024-01-01T00:00:00Z'
    }
    
    vi.mocked(tasksApi.removeDependency).mockResolvedValue(undefined as any)

    const store = useTasksStore()
    store.currentTask = {
      ...mockTask,
      dependencies: [dependencyToRemove]
    }
    
    await store.removeDependency(999, 1)

    expect(store.currentTask?.dependencies).toHaveLength(1)
  })

  it('连续失败操作应正确维护 error 和 loading 状态', async () => {
    const operations = [
      { api: vi.mocked(tasksApi.getTasks), method: 'fetchTasks', args: [] },
      { api: vi.mocked(tasksApi.createTask), method: 'createTask', args: [{ title: 'Test' }] },
      { api: vi.mocked(tasksApi.updateTask), method: 'updateTask', args: [1, { status: 'done' }] },
      { api: vi.mocked(tasksApi.deleteTask), method: 'deleteTask', args: [1] }
    ]

    for (const op of operations) {
      op.api.mockRejectedValueOnce(new Error('Test error'))
      
      const store = useTasksStore()
      
      await expect((store as any)[op.method](...op.args)).rejects.toThrow('Test error')
      expect(store.error).toBe('Test error')
      expect(store.loading).toBe(false)
    }
  })
})
