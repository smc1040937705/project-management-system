import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '@/stores/tasks'
import type { Task, TaskCreate, TaskUpdate, TaskDependencyCreate } from '@/types'

const mockUser = {
  id: 1,
  email: 'creator@example.com',
  username: 'creator',
  first_name: 'Creator',
  last_name: 'User',
  role: 'member' as const,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockAssignee = {
  id: 2,
  email: 'assignee@example.com',
  username: 'assignee',
  first_name: 'Assignee',
  last_name: 'User',
  role: 'member' as const,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockTasks: Task[] = [
  {
    id: 1,
    project_id: 1,
    title: 'Task 1',
    description: 'Description 1',
    status: 'todo',
    priority: 'high',
    assignee_id: 2,
    assignee: mockAssignee,
    created_by: 1,
    creator: mockUser,
    estimated_hours: 8,
    actual_hours: 0,
    due_date: '2024-12-31',
    created_at: '2024-01-01T00:00:00Z',
    subtasks: [],
    dependencies: [],
  },
  {
    id: 2,
    project_id: 1,
    title: 'Task 2',
    description: 'Description 2',
    status: 'in_progress',
    priority: 'medium',
    assignee_id: null,
    assignee: null,
    created_by: 1,
    creator: mockUser,
    estimated_hours: 4,
    actual_hours: 2,
    created_at: '2024-01-02T00:00:00Z',
    subtasks: [],
    dependencies: [],
  },
]

vi.mock('@/api', () => ({
  tasksApi: {
    getTasks: vi.fn(),
    getTask: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
    addDependency: vi.fn(),
    removeDependency: vi.fn(),
  },
}))

import { tasksApi } from '@/api'

describe('useTasksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始状态应该是空的', () => {
      const store = useTasksStore()
      
      expect(store.tasks).toEqual([])
      expect(store.currentTask).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchTasks', () => {
    it('获取任务列表成功', async () => {
      const store = useTasksStore()
      
      vi.mocked(tasksApi.getTasks).mockResolvedValue({
        data: mockTasks,
      } as any)

      const result = await store.fetchTasks()

      expect(tasksApi.getTasks).toHaveBeenCalledWith(undefined)
      expect(store.tasks).toEqual(mockTasks)
      expect(store.loading).toBe(false)
      expect(result).toEqual(mockTasks)
    })

    it('带参数获取任务列表', async () => {
      const store = useTasksStore()
      
      vi.mocked(tasksApi.getTasks).mockResolvedValue({
        data: [mockTasks[0]],
      } as any)

      const params = { project_id: 1, status: 'todo', priority: 'high', assignee_id: 2 }
      const result = await store.fetchTasks(params)

      expect(tasksApi.getTasks).toHaveBeenCalledWith(params)
      expect(store.tasks).toHaveLength(1)
      expect(result).toHaveLength(1)
    })

    it('带搜索参数获取任务列表', async () => {
      const store = useTasksStore()
      
      vi.mocked(tasksApi.getTasks).mockResolvedValue({
        data: [mockTasks[0]],
      } as any)

      const params = { search: 'Task 1' }
      await store.fetchTasks(params)

      expect(tasksApi.getTasks).toHaveBeenCalledWith(params)
    })

    it('获取任务列表失败应设置错误信息', async () => {
      const store = useTasksStore()
      
      const error = new Error('Network error')
      vi.mocked(tasksApi.getTasks).mockRejectedValue(error)

      await expect(store.fetchTasks()).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchTask', () => {
    it('获取单个任务成功', async () => {
      const store = useTasksStore()
      
      vi.mocked(tasksApi.getTask).mockResolvedValue({
        data: mockTasks[0],
      } as any)

      const result = await store.fetchTask(1)

      expect(tasksApi.getTask).toHaveBeenCalledWith(1)
      expect(store.currentTask).toEqual(mockTasks[0])
      expect(result).toEqual(mockTasks[0])
    })

    it('获取不存在的任务应抛出错误', async () => {
      const store = useTasksStore()
      
      const error = new Error('Task not found')
      vi.mocked(tasksApi.getTask).mockRejectedValue(error)

      await expect(store.fetchTask(999)).rejects.toThrow('Task not found')
      expect(store.error).toBe('Task not found')
    })
  })

  describe('createTask', () => {
    it('创建任务成功', async () => {
      const store = useTasksStore()
      const newTaskData: TaskCreate = {
        project_id: 1,
        title: 'New Task',
        description: 'New Description',
        status: 'todo',
        priority: 'medium',
      }

      const createdTask: Task = {
        id: 3,
        ...newTaskData,
        assignee_id: null,
        assignee: null,
        created_by: 1,
        creator: mockUser,
        estimated_hours: undefined,
        actual_hours: 0,
        created_at: '2024-01-03T00:00:00Z',
        subtasks: [],
        dependencies: [],
      }

      vi.mocked(tasksApi.createTask).mockResolvedValue({
        data: createdTask,
      } as any)

      const result = await store.createTask(newTaskData)

      expect(tasksApi.createTask).toHaveBeenCalledWith(newTaskData)
      expect(store.tasks).toContainEqual(createdTask)
      expect(result).toEqual(createdTask)
    })

    it('创建带依赖的任务成功', async () => {
      const store = useTasksStore()
      const dependency: TaskDependencyCreate = {
        depends_on_task_id: 1,
        dependency_type: 'finish_to_start',
      }
      const newTaskData: TaskCreate = {
        project_id: 1,
        title: 'New Task with Dependency',
        status: 'todo',
        priority: 'medium',
        dependencies: [dependency],
      }

      const createdTask: Task = {
        id: 3,
        project_id: 1,
        title: 'New Task with Dependency',
        description: null,
        status: 'todo',
        priority: 'medium',
        assignee_id: null,
        assignee: null,
        created_by: 1,
        creator: mockUser,
        estimated_hours: undefined,
        actual_hours: 0,
        created_at: '2024-01-03T00:00:00Z',
        subtasks: [],
        dependencies: [{
          id: 1,
          task_id: 3,
          depends_on_task_id: 1,
          dependency_type: 'finish_to_start',
          created_at: '2024-01-03T00:00:00Z',
        }],
      }

      vi.mocked(tasksApi.createTask).mockResolvedValue({
        data: createdTask,
      } as any)

      const result = await store.createTask(newTaskData)

      expect(result.dependencies).toHaveLength(1)
    })

    it('创建任务失败应抛出错误', async () => {
      const store = useTasksStore()
      const newTaskData: TaskCreate = {
        project_id: 999,
        title: 'Invalid Task',
        status: 'todo',
        priority: 'medium',
      }

      const error = new Error('Project not found')
      vi.mocked(tasksApi.createTask).mockRejectedValue(error)

      await expect(store.createTask(newTaskData)).rejects.toThrow('Project not found')
      expect(store.error).toBe('Project not found')
    })
  })

  describe('updateTask', () => {
    it('更新任务成功', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      
      const updateData: TaskUpdate = {
        title: 'Updated Task 1',
        status: 'done',
      }

      const updatedTask: Task = {
        ...mockTasks[0],
        ...updateData,
      }

      vi.mocked(tasksApi.updateTask).mockResolvedValue({
        data: updatedTask,
      } as any)

      const result = await store.updateTask(1, updateData)

      expect(tasksApi.updateTask).toHaveBeenCalledWith(1, updateData)
      expect(store.tasks[0]).toEqual(updatedTask)
      expect(result).toEqual(updatedTask)
    })

    it('更新当前任务时应同步更新currentTask', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      store.currentTask = mockTasks[0]
      
      const updateData: TaskUpdate = {
        status: 'done',
      }

      const updatedTask: Task = {
        ...mockTasks[0],
        status: 'done',
      }

      vi.mocked(tasksApi.updateTask).mockResolvedValue({
        data: updatedTask,
      } as any)

      await store.updateTask(1, updateData)

      expect(store.currentTask).toEqual(updatedTask)
    })

    it('更新任务指派人成功', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      
      const updateData: TaskUpdate = {
        assignee_id: 3,
      }

      const updatedTask: Task = {
        ...mockTasks[0],
        assignee_id: 3,
      }

      vi.mocked(tasksApi.updateTask).mockResolvedValue({
        data: updatedTask,
      } as any)

      await store.updateTask(1, updateData)

      expect(store.tasks[0].assignee_id).toBe(3)
    })

    it('清除任务指派人成功', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      
      const updateData: TaskUpdate = {
        assignee_id: null,
      }

      const updatedTask: Task = {
        ...mockTasks[0],
        assignee_id: null,
        assignee: null,
      }

      vi.mocked(tasksApi.updateTask).mockResolvedValue({
        data: updatedTask,
      } as any)

      await store.updateTask(1, updateData)

      expect(store.tasks[0].assignee_id).toBeNull()
    })

    it('更新不存在的任务应抛出错误', async () => {
      const store = useTasksStore()
      
      const error = new Error('Task not found')
      vi.mocked(tasksApi.updateTask).mockRejectedValue(error)

      await expect(store.updateTask(999, { title: 'Test' })).rejects.toThrow('Task not found')
    })
  })

  describe('deleteTask', () => {
    it('删除任务成功', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      
      vi.mocked(tasksApi.deleteTask).mockResolvedValue({} as any)

      await store.deleteTask(1)

      expect(tasksApi.deleteTask).toHaveBeenCalledWith(1)
      expect(store.tasks.find(t => t.id === 1)).toBeUndefined()
      expect(store.tasks).toHaveLength(1)
    })

    it('删除当前任务时应清除currentTask', async () => {
      const store = useTasksStore()
      store.tasks = [...mockTasks]
      store.currentTask = mockTasks[0]
      
      vi.mocked(tasksApi.deleteTask).mockResolvedValue({} as any)

      await store.deleteTask(1)

      expect(store.currentTask).toBeNull()
    })

    it('删除不存在的任务应抛出错误', async () => {
      const store = useTasksStore()
      
      const error = new Error('Task not found')
      vi.mocked(tasksApi.deleteTask).mockRejectedValue(error)

      await expect(store.deleteTask(999)).rejects.toThrow('Task not found')
    })
  })

  describe('addDependency', () => {
    it('添加依赖成功', async () => {
      const store = useTasksStore()
      store.currentTask = mockTasks[0]
      
      const dependencyData: TaskDependencyCreate = {
        depends_on_task_id: 2,
        dependency_type: 'finish_to_start',
      }

      const newDependency = {
        id: 1,
        task_id: 1,
        depends_on_task_id: 2,
        dependency_type: 'finish_to_start',
        created_at: '2024-01-03T00:00:00Z',
      }

      vi.mocked(tasksApi.addDependency).mockResolvedValue({
        data: newDependency,
      } as any)

      const result = await store.addDependency(1, dependencyData)

      expect(tasksApi.addDependency).toHaveBeenCalledWith(1, dependencyData)
      expect(store.currentTask?.dependencies).toContainEqual(newDependency)
      expect(result).toEqual(newDependency)
    })

    it('添加依赖到非当前任务不应更新currentTask', async () => {
      const store = useTasksStore()
      store.currentTask = {
        ...mockTasks[0],
        dependencies: [],
      }
      
      const dependencyData: TaskDependencyCreate = {
        depends_on_task_id: 1,
      }

      const newDependency = {
        id: 2,
        task_id: 2,
        depends_on_task_id: 1,
        dependency_type: 'finish_to_start',
        created_at: '2024-01-03T00:00:00Z',
      }

      vi.mocked(tasksApi.addDependency).mockResolvedValue({
        data: newDependency,
      } as any)

      await store.addDependency(2, dependencyData)

      expect(store.currentTask?.dependencies).toHaveLength(0)
    })

    it('添加循环依赖应抛出错误', async () => {
      const store = useTasksStore()
      
      const error = new Error('Circular dependency detected')
      vi.mocked(tasksApi.addDependency).mockRejectedValue(error)

      await expect(store.addDependency(1, { depends_on_task_id: 2 })).rejects.toThrow('Circular dependency detected')
    })
  })

  describe('removeDependency', () => {
    it('移除依赖成功', async () => {
      const taskWithDependency: Task = {
        ...mockTasks[0],
        dependencies: [{
          id: 1,
          task_id: 1,
          depends_on_task_id: 2,
          dependency_type: 'finish_to_start',
          created_at: '2024-01-03T00:00:00Z',
        }],
      }
      const store = useTasksStore()
      store.currentTask = taskWithDependency
      
      vi.mocked(tasksApi.removeDependency).mockResolvedValue({} as any)

      await store.removeDependency(1, 1)

      expect(tasksApi.removeDependency).toHaveBeenCalledWith(1, 1)
      expect(store.currentTask?.dependencies).toHaveLength(0)
    })

    it('移除不存在的依赖应抛出错误', async () => {
      const store = useTasksStore()
      
      const error = new Error('Dependency not found')
      vi.mocked(tasksApi.removeDependency).mockRejectedValue(error)

      await expect(store.removeDependency(1, 999)).rejects.toThrow('Dependency not found')
    })
  })

  describe('loading状态', () => {
    it('操作过程中应正确设置loading状态', async () => {
      const store = useTasksStore()
      
      vi.mocked(tasksApi.getTasks).mockImplementation(() => {
        expect(store.loading).toBe(true)
        return Promise.resolve({ data: mockTasks } as any)
      })

      const promise = store.fetchTasks()
      expect(store.loading).toBe(true)
      
      await promise
      expect(store.loading).toBe(false)
    })
  })
})
