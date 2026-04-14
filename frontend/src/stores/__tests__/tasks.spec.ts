import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '../tasks'
import type { Task, TaskCreate, TaskUpdate, TaskDependencyCreate } from '@/types'

// Mock API模块
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

import { tasksApi } from '@/api'

describe('Tasks Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mockTask: Task = {
    id: 1,
    project_id: 1,
    title: 'Test Task',
    description: 'Test Description',
    status: 'todo',
    priority: 'high',
    assignee_id: 1,
    assignee: {
      id: 1,
      email: 'assignee@example.com',
      username: 'assignee',
      first_name: 'Assignee',
      last_name: 'User',
      role: 'member',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    created_by: 2,
    creator: {
      id: 2,
      email: 'creator@example.com',
      username: 'creator',
      first_name: 'Creator',
      last_name: 'User',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    actual_hours: 0,
    created_at: '2024-01-01T00:00:00Z',
    subtasks: [],
    dependencies: []
  }

  /**
   * 测试场景：store初始化
   * 验证：初始状态正确
   */
  it('should initialize with default state', () => {
    const store = useTasksStore()

    expect(store.tasks).toEqual([])
    expect(store.currentTask).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  /**
   * 测试场景：正常获取任务列表
   * 验证：任务列表被正确更新
   */
  it('should fetch tasks successfully', async () => {
    const mockTasks = [mockTask]
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: mockTasks })

    const store = useTasksStore()
    const params = { project_id: 1, status: 'todo' }

    const result = await store.fetchTasks(params)

    expect(tasksApi.getTasks).toHaveBeenCalledWith(params)
    expect(result).toEqual(mockTasks)
    expect(store.tasks).toEqual(mockTasks)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  /**
   * 测试场景：获取任务列表失败
   * 验证：错误状态被设置
   */
  it('should handle fetch tasks error', async () => {
    vi.mocked(tasksApi.getTasks).mockRejectedValue(new Error('Failed to fetch tasks'))

    const store = useTasksStore()

    await expect(store.fetchTasks()).rejects.toThrow('Failed to fetch tasks')

    expect(store.tasks).toEqual([])
    expect(store.error).toBe('Failed to fetch tasks')
    expect(store.loading).toBe(false)
  })

  /**
   * 测试场景：正常获取单个任务
   * 验证：当前任务被正确更新
   */
  it('should fetch single task successfully', async () => {
    vi.mocked(tasksApi.getTask).mockResolvedValue({ data: mockTask })

    const store = useTasksStore()

    const result = await store.fetchTask(1)

    expect(tasksApi.getTask).toHaveBeenCalledWith(1)
    expect(result).toEqual(mockTask)
    expect(store.currentTask).toEqual(mockTask)
  })

  /**
   * 测试场景：获取单个任务失败
   * 验证：错误状态被设置
   */
  it('should handle fetch task not found error', async () => {
    vi.mocked(tasksApi.getTask).mockRejectedValue(new Error('Task not found'))

    const store = useTasksStore()

    await expect(store.fetchTask(999)).rejects.toThrow('Task not found')

    expect(store.currentTask).toBeNull()
    expect(store.error).toBe('Task not found')
  })

  /**
   * 测试场景：正常创建任务
   * 验证：新任务被添加到列表
   */
  it('should create task successfully', async () => {
    const newTask: Task = {
      ...mockTask,
      id: 2,
      title: 'New Task'
    }
    vi.mocked(tasksApi.createTask).mockResolvedValue({ data: newTask })

    const store = useTasksStore()
    store.tasks = [mockTask]

    const taskData: TaskCreate = {
      project_id: 1,
      title: 'New Task',
      status: 'todo',
      priority: 'medium'
    }

    const result = await store.createTask(taskData)

    expect(tasksApi.createTask).toHaveBeenCalledWith(taskData)
    expect(result).toEqual(newTask)
    expect(store.tasks).toHaveLength(2)
    expect(store.tasks[1]).toEqual(newTask)
  })

  /**
   * 测试场景：创建任务失败
   * 验证：错误被抛出
   */
  it('should handle create task error', async () => {
    vi.mocked(tasksApi.createTask).mockRejectedValue(new Error('Project not found'))

    const store = useTasksStore()

    const taskData: TaskCreate = {
      project_id: 999,
      title: 'New Task',
      status: 'todo',
      priority: 'medium'
    }

    await expect(store.createTask(taskData)).rejects.toThrow('Project not found')

    expect(store.error).toBe('Project not found')
  })

  /**
   * 测试场景：正常更新任务
   * 验证：任务列表和当前任务都被更新
   */
  it('should update task successfully', async () => {
    const updatedTask: Task = {
      ...mockTask,
      title: 'Updated Task Title',
      status: 'in_progress'
    }
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: updatedTask })

    const store = useTasksStore()
    store.tasks = [mockTask]
    store.currentTask = mockTask

    const updateData: TaskUpdate = {
      title: 'Updated Task Title',
      status: 'in_progress'
    }

    const result = await store.updateTask(1, updateData)

    expect(tasksApi.updateTask).toHaveBeenCalledWith(1, updateData)
    expect(result).toEqual(updatedTask)
    expect(store.tasks[0].title).toBe('Updated Task Title')
    expect(store.currentTask?.title).toBe('Updated Task Title')
  })

  /**
   * 测试场景：更新任务状态为完成
   * 验证：任务状态正确更新
   */
  it('should update task status to done', async () => {
    const completedTask: Task = {
      ...mockTask,
      status: 'done',
      completed_at: '2024-01-15T00:00:00Z'
    }
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: completedTask })

    const store = useTasksStore()
    store.tasks = [mockTask]

    const result = await store.updateTask(1, { status: 'done' })

    expect(result.status).toBe('done')
    expect(store.tasks[0].status).toBe('done')
  })

  /**
   * 测试场景：更新任务分配人
   * 验证：分配人正确更新
   */
  it('should update task assignee', async () => {
    const updatedTask: Task = {
      ...mockTask,
      assignee_id: 3,
      assignee: {
        id: 3,
        email: 'new@example.com',
        username: 'newuser',
        first_name: 'New',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }
    }
    vi.mocked(tasksApi.updateTask).mockResolvedValue({ data: updatedTask })

    const store = useTasksStore()
    store.tasks = [mockTask]

    const result = await store.updateTask(1, { assignee_id: 3 })

    expect(result.assignee_id).toBe(3)
  })

  /**
   * 测试场景：更新不存在的任务
   * 验证：错误被抛出
   */
  it('should handle update non-existent task', async () => {
    vi.mocked(tasksApi.updateTask).mockRejectedValue(new Error('Task not found'))

    const store = useTasksStore()

    await expect(store.updateTask(999, { title: 'New' })).rejects.toThrow('Task not found')

    expect(store.error).toBe('Task not found')
  })

  /**
   * 测试场景：正常删除任务
   * 验证：任务从列表中移除
   */
  it('should delete task successfully', async () => {
    vi.mocked(tasksApi.deleteTask).mockResolvedValue({ data: undefined })

    const store = useTasksStore()
    store.tasks = [mockTask]
    store.currentTask = mockTask

    await store.deleteTask(1)

    expect(tasksApi.deleteTask).toHaveBeenCalledWith(1)
    expect(store.tasks).toHaveLength(0)
    expect(store.currentTask).toBeNull()
  })

  /**
   * 测试场景：删除任务失败（权限不足）
   * 验证：错误被抛出，任务列表不变
   */
  it('should handle delete task permission error', async () => {
    vi.mocked(tasksApi.deleteTask).mockRejectedValue(new Error('Permission denied'))

    const store = useTasksStore()
    store.tasks = [mockTask]

    await expect(store.deleteTask(1)).rejects.toThrow('Permission denied')

    expect(store.tasks).toHaveLength(1)
    expect(store.error).toBe('Permission denied')
  })

  /**
   * 测试场景：删除非当前任务
   * 验证：只从列表移除，当前任务不变
   */
  it('should delete task without affecting current task if different', async () => {
    vi.mocked(tasksApi.deleteTask).mockResolvedValue({ data: undefined })

    const store = useTasksStore()
    const anotherTask: Task = { ...mockTask, id: 2 }
    store.tasks = [mockTask, anotherTask]
    store.currentTask = mockTask

    await store.deleteTask(2)

    expect(store.tasks).toHaveLength(1)
    expect(store.currentTask).toEqual(mockTask)
  })

  /**
   * 测试场景：正常添加任务依赖
   * 验证：依赖被添加到当前任务
   */
  it('should add dependency successfully', async () => {
    const dependency = {
      id: 1,
      task_id: 1,
      depends_on_task_id: 2,
      dependency_type: 'finish_to_start',
      created_at: '2024-01-01T00:00:00Z'
    }
    vi.mocked(tasksApi.addDependency).mockResolvedValue({ data: dependency })

    const store = useTasksStore()
    store.currentTask = mockTask

    const depData: TaskDependencyCreate = {
      depends_on_task_id: 2,
      dependency_type: 'finish_to_start'
    }

    const result = await store.addDependency(1, depData)

    expect(tasksApi.addDependency).toHaveBeenCalledWith(1, depData)
    expect(result).toEqual(dependency)
    expect(store.currentTask?.dependencies).toContainEqual(dependency)
  })

  /**
   * 测试场景：添加依赖到非当前任务
   * 验证：当前任务不变
   */
  it('should add dependency without affecting current task if different', async () => {
    const dependency = {
      id: 1,
      task_id: 2,
      depends_on_task_id: 3,
      dependency_type: 'finish_to_start',
      created_at: '2024-01-01T00:00:00Z'
    }
    vi.mocked(tasksApi.addDependency).mockResolvedValue({ data: dependency })

    const store = useTasksStore()
    // 设置当前任务为不同ID的任务
    store.currentTask = { ...mockTask, id: 1, dependencies: [] }

    await store.addDependency(2, { depends_on_task_id: 3 })

    // 当前任务（ID=1）不应该被修改，因为依赖是添加到任务ID=2
    expect(store.currentTask.dependencies).toEqual([])
  })

  /**
   * 测试场景：正常移除任务依赖
   * 验证：依赖从当前任务移除
   */
  it('should remove dependency successfully', async () => {
    const taskWithDep: Task = {
      ...mockTask,
      dependencies: [{
        id: 1,
        task_id: 1,
        depends_on_task_id: 2,
        dependency_type: 'finish_to_start',
        created_at: '2024-01-01T00:00:00Z'
      }]
    }
    vi.mocked(tasksApi.removeDependency).mockResolvedValue({ data: undefined })

    const store = useTasksStore()
    store.currentTask = taskWithDep

    await store.removeDependency(1, 1)

    expect(tasksApi.removeDependency).toHaveBeenCalledWith(1, 1)
    expect(store.currentTask?.dependencies).toHaveLength(0)
  })

  /**
   * 测试场景：移除依赖时当前任务无此依赖
   * 验证：操作正常完成
   */
  it('should handle remove dependency when not in current task', async () => {
    vi.mocked(tasksApi.removeDependency).mockResolvedValue({ data: undefined })

    const store = useTasksStore()
    // 设置当前任务，其依赖列表中不包含ID为999的依赖
    store.currentTask = { ...mockTask, id: 1, dependencies: [{ id: 1, task_id: 1, depends_on_task_id: 2, dependency_type: 'finish_to_start', created_at: '2024-01-01T00:00:00Z' }] }

    await store.removeDependency(1, 999)

    // 当前任务的依赖列表应该保持不变（因为没有ID为999的依赖）
    expect(store.currentTask?.dependencies).toHaveLength(1)
  })

  /**
   * 测试场景：loading状态正确管理
   * 验证：异步操作期间loading为true
   */
  it('should manage loading state correctly', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: [] })

    const store = useTasksStore()

    expect(store.loading).toBe(false)

    const promise = store.fetchTasks()
    expect(store.loading).toBe(true)

    await promise
    expect(store.loading).toBe(false)
  })

  /**
   * 测试场景：带搜索参数获取任务
   * 验证：搜索参数被正确传递
   */
  it('should fetch tasks with search params', async () => {
    vi.mocked(tasksApi.getTasks).mockResolvedValue({ data: [] })

    const store = useTasksStore()
    const params = {
      project_id: 1,
      status: 'in_progress',
      priority: 'high',
      assignee_id: 1,
      search: 'test'
    }

    await store.fetchTasks(params)

    expect(tasksApi.getTasks).toHaveBeenCalledWith(params)
  })
})
