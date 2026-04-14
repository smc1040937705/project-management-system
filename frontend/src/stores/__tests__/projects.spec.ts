import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectsStore } from '../projects'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types'

// Mock API模块
vi.mock('@/api', () => ({
  projectsApi: {
    getProjects: vi.fn(),
    getProject: vi.fn(),
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn()
  }
}))

import { projectsApi } from '@/api'

describe('Projects Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  const mockProject: Project = {
    id: 1,
    name: 'Test Project',
    description: 'Test Description',
    status: 'active',
    owner_id: 1,
    owner: {
      id: 1,
      email: 'owner@example.com',
      username: 'owner',
      first_name: 'Owner',
      last_name: 'User',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    members: [],
    created_at: '2024-01-01T00:00:00Z',
    task_count: 0,
    completed_task_count: 0
  }

  /**
   * 测试场景：store初始化
   * 验证：初始状态正确
   */
  it('should initialize with default state', () => {
    const store = useProjectsStore()

    expect(store.projects).toEqual([])
    expect(store.currentProject).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  /**
   * 测试场景：正常获取项目列表
   * 验证：项目列表被正确更新，loading状态正确
   */
  it('should fetch projects successfully', async () => {
    const mockProjects = [mockProject]
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: mockProjects })

    const store = useProjectsStore()
    const params = { skip: 0, limit: 20 }

    const promise = store.fetchProjects(params)
    expect(store.loading).toBe(true)

    const result = await promise

    expect(projectsApi.getProjects).toHaveBeenCalledWith(params)
    expect(result).toEqual(mockProjects)
    expect(store.projects).toEqual(mockProjects)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  /**
   * 测试场景：获取项目列表失败
   * 验证：错误状态被设置，loading状态重置
   */
  it('should handle fetch projects error', async () => {
    vi.mocked(projectsApi.getProjects).mockRejectedValue(new Error('Network error'))

    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow('Network error')

    expect(store.projects).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Network error')
  })

  /**
   * 测试场景：正常获取单个项目
   * 验证：当前项目被正确更新
   */
  it('should fetch single project successfully', async () => {
    vi.mocked(projectsApi.getProject).mockResolvedValue({ data: mockProject })

    const store = useProjectsStore()

    const result = await store.fetchProject(1)

    expect(projectsApi.getProject).toHaveBeenCalledWith(1)
    expect(result).toEqual(mockProject)
    expect(store.currentProject).toEqual(mockProject)
    expect(store.loading).toBe(false)
  })

  /**
   * 测试场景：获取单个项目失败（项目不存在）
   * 验证：错误状态被设置
   */
  it('should handle fetch project not found error', async () => {
    vi.mocked(projectsApi.getProject).mockRejectedValue(new Error('Project not found'))

    const store = useProjectsStore()

    await expect(store.fetchProject(999)).rejects.toThrow('Project not found')

    expect(store.currentProject).toBeNull()
    expect(store.error).toBe('Project not found')
  })

  /**
   * 测试场景：正常创建项目
   * 验证：新项目被添加到列表
   */
  it('should create project successfully', async () => {
    const newProject: Project = {
      ...mockProject,
      id: 2,
      name: 'New Project'
    }
    vi.mocked(projectsApi.createProject).mockResolvedValue({ data: newProject })

    const store = useProjectsStore()
    store.projects = [mockProject]

    const projectData: ProjectCreate = {
      name: 'New Project',
      description: 'New Description',
      status: 'planning'
    }

    const result = await store.createProject(projectData)

    expect(projectsApi.createProject).toHaveBeenCalledWith(projectData)
    expect(result).toEqual(newProject)
    expect(store.projects).toHaveLength(2)
    expect(store.projects[1]).toEqual(newProject)
  })

  /**
   * 测试场景：创建项目失败（验证错误）
   * 验证：错误被抛出，列表不变
   */
  it('should handle create project validation error', async () => {
    vi.mocked(projectsApi.createProject).mockRejectedValue(new Error('Name is required'))

    const store = useProjectsStore()

    const projectData: ProjectCreate = {
      name: '',
      status: 'planning'
    }

    await expect(store.createProject(projectData)).rejects.toThrow('Name is required')

    expect(store.projects).toEqual([])
    expect(store.error).toBe('Name is required')
  })

  /**
   * 测试场景：正常更新项目
   * 验证：项目列表和当前项目都被更新
   */
  it('should update project successfully', async () => {
    const updatedProject: Project = {
      ...mockProject,
      name: 'Updated Project Name'
    }
    vi.mocked(projectsApi.updateProject).mockResolvedValue({ data: updatedProject })

    const store = useProjectsStore()
    store.projects = [mockProject]
    store.currentProject = mockProject

    const updateData: ProjectUpdate = { name: 'Updated Project Name' }

    const result = await store.updateProject(1, updateData)

    expect(projectsApi.updateProject).toHaveBeenCalledWith(1, updateData)
    expect(result).toEqual(updatedProject)
    expect(store.projects[0].name).toBe('Updated Project Name')
    expect(store.currentProject?.name).toBe('Updated Project Name')
  })

  /**
   * 测试场景：更新不存在的项目
   * 验证：错误被抛出
   */
  it('should handle update non-existent project', async () => {
    vi.mocked(projectsApi.updateProject).mockRejectedValue(new Error('Project not found'))

    const store = useProjectsStore()

    await expect(store.updateProject(999, { name: 'New Name' })).rejects.toThrow('Project not found')

    expect(store.error).toBe('Project not found')
  })

  /**
   * 测试场景：正常删除项目
   * 验证：项目从列表中移除，当前项目被清空
   */
  it('should delete project successfully', async () => {
    vi.mocked(projectsApi.deleteProject).mockResolvedValue({ data: undefined })

    const store = useProjectsStore()
    store.projects = [mockProject]
    store.currentProject = mockProject

    await store.deleteProject(1)

    expect(projectsApi.deleteProject).toHaveBeenCalledWith(1)
    expect(store.projects).toHaveLength(0)
    expect(store.currentProject).toBeNull()
  })

  /**
   * 测试场景：删除项目失败（权限不足）
   * 验证：错误被抛出，项目列表不变
   */
  it('should handle delete project permission error', async () => {
    vi.mocked(projectsApi.deleteProject).mockRejectedValue(new Error('Permission denied'))

    const store = useProjectsStore()
    store.projects = [mockProject]

    await expect(store.deleteProject(1)).rejects.toThrow('Permission denied')

    expect(store.projects).toHaveLength(1)
    expect(store.error).toBe('Permission denied')
  })

  /**
   * 测试场景：删除非当前项目
   * 验证：只从列表移除，当前项目不变
   */
  it('should delete project without affecting current project if different', async () => {
    vi.mocked(projectsApi.deleteProject).mockResolvedValue({ data: undefined })

    const store = useProjectsStore()
    const anotherProject: Project = { ...mockProject, id: 2 }
    store.projects = [mockProject, anotherProject]
    store.currentProject = mockProject

    await store.deleteProject(2)

    expect(store.projects).toHaveLength(1)
    expect(store.currentProject).toEqual(mockProject)
  })

  /**
   * 测试场景：正常添加项目成员
   * 验证：当前项目成员更新
   */
  it('should add member to project successfully', async () => {
    const updatedProject: Project = {
      ...mockProject,
      members: [{
        id: 2,
        email: 'member@example.com',
        username: 'member',
        first_name: 'Member',
        last_name: 'User',
        role: 'member',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z'
      }]
    }
    vi.mocked(projectsApi.addMember).mockResolvedValue({ data: updatedProject })

    const store = useProjectsStore()
    store.currentProject = mockProject

    const result = await store.addMember(1, 2)

    expect(projectsApi.addMember).toHaveBeenCalledWith(1, 2)
    expect(result).toEqual(updatedProject)
    expect(store.currentProject?.members).toHaveLength(1)
  })

  /**
   * 测试场景：添加成员到非当前项目
   * 验证：当前项目不变
   */
  it('should add member without affecting current project if different', async () => {
    const updatedProject: Project = {
      ...mockProject,
      id: 2,
      members: [{ id: 3, email: 'other@example.com', username: 'other', first_name: 'Other', last_name: 'User', role: 'member', is_active: true, created_at: '2024-01-01T00:00:00Z' }]
    }
    vi.mocked(projectsApi.addMember).mockResolvedValue({ data: updatedProject })

    const store = useProjectsStore()
    store.currentProject = mockProject

    await store.addMember(2, 3)

    expect(store.currentProject).toEqual(mockProject)
  })

  /**
   * 测试场景：正常移除项目成员
   * 验证：成员从当前项目移除
   */
  it('should remove member from project successfully', async () => {
    const projectWithMember: Project = {
      ...mockProject,
      members: [{ id: 2, email: 'member@example.com', username: 'member', first_name: 'Member', last_name: 'User', role: 'member', is_active: true, created_at: '2024-01-01T00:00:00Z' }]
    }
    const updatedProject: Project = {
      ...mockProject,
      members: []
    }
    vi.mocked(projectsApi.removeMember).mockResolvedValue({ data: updatedProject })

    const store = useProjectsStore()
    store.currentProject = projectWithMember

    const result = await store.removeMember(1, 2)

    expect(projectsApi.removeMember).toHaveBeenCalledWith(1, 2)
    expect(result).toEqual(updatedProject)
    expect(store.currentProject?.members).toHaveLength(0)
  })

  /**
   * 测试场景：loading状态正确管理
   * 验证：异步操作期间loading为true，完成后为false
   */
  it('should manage loading state correctly', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: [] })

    const store = useProjectsStore()

    expect(store.loading).toBe(false)

    const promise = store.fetchProjects()
    expect(store.loading).toBe(true)

    await promise
    expect(store.loading).toBe(false)
  })

  /**
   * 测试场景：错误状态正确重置
   * 验证：新操作前错误被清空
   */
  it('should clear error before new operations', async () => {
    vi.mocked(projectsApi.getProjects)
      .mockRejectedValueOnce(new Error('First error'))
      .mockResolvedValueOnce({ data: [] })

    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow()
    expect(store.error).toBe('First error')

    await store.fetchProjects()
    expect(store.error).toBeNull()
  })
})
