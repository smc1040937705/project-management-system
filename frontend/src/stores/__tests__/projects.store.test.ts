import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectsStore } from '../projects'
import { projectsApi } from '@/api'

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

const mockProject = {
  id: 1,
  name: 'Test Project',
  description: 'Test Description',
  status: 'active',
  owner_id: 1,
  owner: { id: 1, username: 'owner' },
  members: [],
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  budget: 10000,
  task_count: 5,
  completed_task_count: 2,
  created_at: '2024-01-01T00:00:00Z'
}

const mockProjects = [
  mockProject,
  {
    id: 2,
    name: 'Second Project',
    description: 'Another project',
    status: 'active',
    owner_id: 1,
    owner: { id: 1, username: 'owner' },
    members: [],
    task_count: 3,
    completed_task_count: 1,
    created_at: '2024-01-02T00:00:00Z'
  }
]

describe('Projects Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    const store = useProjectsStore()
    store.projects = []
    store.currentProject = null
    store.error = null
    store.loading = false
  })

  it('初始化时项目列表应为空', () => {
    const store = useProjectsStore()
    expect(store.projects).toEqual([])
    expect(store.currentProject).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchProjects 成功时应更新项目列表', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: mockProjects } as any)

    const store = useProjectsStore()
    const result = await store.fetchProjects()

    expect(projectsApi.getProjects).toHaveBeenCalledWith(undefined)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.projects).toEqual(mockProjects)
    expect(result).toEqual(mockProjects)
  })

  it('fetchProjects 应带参数调用 API', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: mockProjects } as any)

    const store = useProjectsStore()
    const params = { skip: 0, limit: 10, status: 'active', search: 'Test' }
    await store.fetchProjects(params)

    expect(projectsApi.getProjects).toHaveBeenCalledWith(params)
  })

  it('fetchProjects 失败时应设置错误', async () => {
    const mockError = new Error('Network error')
    vi.mocked(projectsApi.getProjects).mockRejectedValue(mockError)

    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow('Network error')
    
    expect(store.loading).toBe(false)
    expect(store.error).toBe('Network error')
    expect(store.projects).toEqual([])
  })

  it('fetchProjects 应正确设置 loading 状态', async () => {
    let resolvePromise: (value: any) => void
    const pendingPromise = new Promise((resolve) => {
      resolvePromise = resolve
    })
    
    vi.mocked(projectsApi.getProjects).mockReturnValue(pendingPromise as any)

    const store = useProjectsStore()
    const fetchPromise = store.fetchProjects()
    
    expect(store.loading).toBe(true)
    
    resolvePromise!({ data: mockProjects })
    await fetchPromise
    
    expect(store.loading).toBe(false)
  })

  it('fetchProject 成功时应设置 currentProject', async () => {
    vi.mocked(projectsApi.getProject).mockResolvedValue({ data: mockProject } as any)

    const store = useProjectsStore()
    const result = await store.fetchProject(1)

    expect(projectsApi.getProject).toHaveBeenCalledWith(1)
    expect(store.currentProject).toEqual(mockProject)
    expect(result).toEqual(mockProject)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchProject 项目不存在时应抛出异常', async () => {
    const mockError = new Error('Project not found')
    vi.mocked(projectsApi.getProject).mockRejectedValue(mockError)

    const store = useProjectsStore()

    await expect(store.fetchProject(999)).rejects.toThrow('Project not found')
    
    expect(store.currentProject).toBeNull()
    expect(store.error).toBe('Project not found')
  })

  it('createProject 成功时应添加到项目列表', async () => {
    const newProjectData = {
      name: 'New Project',
      description: 'New Description',
      status: 'active',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      budget: 5000,
      member_ids: []
    }

    const createdProject = { ...mockProject, id: 3, name: 'New Project' }
    vi.mocked(projectsApi.createProject).mockResolvedValue({ data: createdProject } as any)

    const store = useProjectsStore()
    store.projects = [...mockProjects]
    
    const result = await store.createProject(newProjectData)

    expect(projectsApi.createProject).toHaveBeenCalledWith(newProjectData)
    expect(store.projects).toContainEqual(createdProject)
    expect(store.projects.length).toBe(3)
    expect(result).toEqual(createdProject)
  })

  it('createProject 失败时不应修改项目列表', async () => {
    const mockError = new Error('Validation failed')
    vi.mocked(projectsApi.createProject).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.projects = [...mockProjects]

    await expect(
      store.createProject({ name: '', description: '', status: 'active' } as any)
    ).rejects.toThrow('Validation failed')
    
    expect(store.projects.length).toBe(2)
    expect(store.error).toBe('Validation failed')
  })

  it('updateProject 成功时应更新项目列表', async () => {
    const updateData = { name: 'Updated Project', description: 'Updated Description' }
    const updatedProject = { ...mockProject, ...updateData }
    
    vi.mocked(projectsApi.updateProject).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.projects = [...mockProjects]
    
    const result = await store.updateProject(1, updateData)

    expect(projectsApi.updateProject).toHaveBeenCalledWith(1, updateData)
    expect(store.projects.find(p => p.id === 1)?.name).toBe('Updated Project')
    expect(result).toEqual(updatedProject)
  })

  it('updateProject 应更新 currentProject 如果匹配', async () => {
    const updateData = { name: 'Updated Project' }
    const updatedProject = { ...mockProject, ...updateData }
    
    vi.mocked(projectsApi.updateProject).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    await store.updateProject(1, updateData)

    expect(store.currentProject?.name).toBe('Updated Project')
  })

  it('updateProject 项目不存在时应抛出异常', async () => {
    const mockError = new Error('Project not found')
    vi.mocked(projectsApi.updateProject).mockRejectedValue(mockError)

    const store = useProjectsStore()

    await expect(
      store.updateProject(999, { name: 'Test' })
    ).rejects.toThrow('Project not found')
  })

  it('deleteProject 成功时应从列表移除', async () => {
    vi.mocked(projectsApi.deleteProject).mockResolvedValue(undefined as any)

    const store = useProjectsStore()
    store.projects = [...mockProjects]
    
    await store.deleteProject(1)

    expect(projectsApi.deleteProject).toHaveBeenCalledWith(1)
    expect(store.projects.find(p => p.id === 1)).toBeUndefined()
    expect(store.projects.length).toBe(1)
  })

  it('deleteProject 应清空 currentProject 如果匹配', async () => {
    vi.mocked(projectsApi.deleteProject).mockResolvedValue(undefined as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    await store.deleteProject(1)

    expect(store.currentProject).toBeNull()
  })

  it('deleteProject 失败时应抛出异常', async () => {
    const mockError = new Error('Permission denied')
    vi.mocked(projectsApi.deleteProject).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.projects = [...mockProjects]

    await expect(store.deleteProject(1)).rejects.toThrow('Permission denied')
    
    expect(store.projects.length).toBe(2)
    expect(store.error).toBe('Permission denied')
  })

  it('addMember 应更新 currentProject', async () => {
    const mockUser = { id: 2, username: 'newmember' }
    const updatedProject = {
      ...mockProject,
      members: [...mockProject.members, mockUser]
    }
    
    vi.mocked(projectsApi.addMember).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    const result = await store.addMember(1, 2)

    expect(projectsApi.addMember).toHaveBeenCalledWith(1, 2)
    expect(result).toEqual(updatedProject)
    expect(store.currentProject?.members).toContainEqual(mockUser)
  })

  it('removeMember 应更新 currentProject', async () => {
    const mockUser = { id: 2, username: 'member' }
    const projectWithMember = {
      ...mockProject,
      members: [mockUser]
    }
    const updatedProject = {
      ...mockProject,
      members: []
    }
    
    vi.mocked(projectsApi.removeMember).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.currentProject = projectWithMember
    
    const result = await store.removeMember(1, 2)

    expect(projectsApi.removeMember).toHaveBeenCalledWith(1, 2)
    expect(result).toEqual(updatedProject)
  })

  it('多次操作应独立处理 loading 状态', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: mockProjects } as any)
    vi.mocked(projectsApi.getProject).mockResolvedValue({ data: mockProject } as any)

    const store = useProjectsStore()
    
    await store.fetchProjects()
    expect(store.loading).toBe(false)
    
    await store.fetchProject(1)
    expect(store.loading).toBe(false)
  })

  it('空状态下项目列表和当前项目应为空', () => {
    const store = useProjectsStore()
    
    expect(store.projects).toEqual([])
    expect(store.currentProject).toBeNull()
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('fetchProjects 权限不足应设置错误并保持空列表', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(projectsApi.getProjects).mockRejectedValue(mockError)

    const store = useProjectsStore()

    await expect(store.fetchProjects()).rejects.toThrow('Not enough permissions')
    
    expect(store.error).toBe('Not enough permissions')
    expect(store.projects).toEqual([])
    expect(store.loading).toBe(false)
  })

  it('fetchProjects 参数校验失败应抛出异常', async () => {
    const mockError = new Error('Validation failed: limit must be between 1 and 100')
    vi.mocked(projectsApi.getProjects).mockRejectedValue(mockError)

    const store = useProjectsStore()

    await expect(
      store.fetchProjects({ limit: 999 })
    ).rejects.toThrow('Validation failed')
    
    expect(store.error).toBe('Validation failed: limit must be between 1 and 100')
  })

  it('createProject 参数校验失败应抛出异常并保持项目列表', async () => {
    const mockError = new Error('Name is required')
    vi.mocked(projectsApi.createProject).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.projects = [...mockProjects]

    await expect(
      store.createProject({ name: '', description: '' } as any)
    ).rejects.toThrow('Name is required')
    
    expect(store.error).toBe('Name is required')
    expect(store.projects.length).toBe(2)
    expect(store.loading).toBe(false)
  })

  it('updateProject 权限不足应抛出异常并保持原有数据', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(projectsApi.updateProject).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.projects = [...mockProjects]
    const originalName = store.projects[0].name

    await expect(
      store.updateProject(1, { name: 'Hacked' })
    ).rejects.toThrow('Not enough permissions')
    
    expect(store.projects[0].name).toBe(originalName)
    expect(store.error).toBe('Not enough permissions')
  })

  it('addMember 用户已存在应抛出异常', async () => {
    const mockError = new Error('User is already a member of this project')
    vi.mocked(projectsApi.addMember).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.currentProject = { ...mockProject, members: [] }

    await expect(
      store.addMember(1, 1)
    ).rejects.toThrow('User is already a member of this project')
    
    expect(store.error).toBe('User is already a member of this project')
  })

  it('removeMember 用户不存在应抛出异常', async () => {
    const mockError = new Error('User is not a member of this project')
    vi.mocked(projectsApi.removeMember).mockRejectedValue(mockError)

    const store = useProjectsStore()
    store.currentProject = { ...mockProject, members: [] }

    await expect(
      store.removeMember(1, 999)
    ).rejects.toThrow('User is not a member of this project')
    
    expect(store.error).toBe('User is not a member of this project')
  })

  it('addMember 非 currentProject 不影响 store 状态', async () => {
    const mockUser = { id: 2, username: 'newmember' }
    const updatedProject = {
      ...mockProject,
      id: 999,
      members: [...mockProject.members, mockUser]
    }
    
    vi.mocked(projectsApi.addMember).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    await store.addMember(999, 2)

    expect(store.currentProject?.members).toHaveLength(0)
  })

  it('removeMember 非 currentProject 不影响 store 状态', async () => {
    vi.mocked(projectsApi.removeMember).mockResolvedValue({ data: mockProject } as any)

    const store = useProjectsStore()
    const originalMembers = [{ id: 2, username: 'member' }]
    store.currentProject = { ...mockProject, members: originalMembers }
    
    await store.removeMember(999, 2)

    expect(store.currentProject?.members).toHaveLength(1)
  })

  it('连续多个失败操作应正确更新 error 状态', async () => {
    const errors = ['Network Error', 'Permission denied', 'Project not found']
    
    for (const errorMsg of errors) {
      vi.mocked(projectsApi.getProjects).mockRejectedValueOnce(new Error(errorMsg))
      
      const store = useProjectsStore()
      
      await expect(store.fetchProjects()).rejects.toThrow(errorMsg)
      expect(store.error).toBe(errorMsg)
      expect(store.loading).toBe(false)
    }
  })

  it('fetchProjects 返回空列表应正确处理', async () => {
    vi.mocked(projectsApi.getProjects).mockResolvedValue({ data: [] } as any)

    const store = useProjectsStore()
    
    const result = await store.fetchProjects()

    expect(result).toEqual([])
    expect(store.projects).toEqual([])
    expect(store.error).toBeNull()
  })

  it('非匹配 ID 的更新不影响 currentProject', async () => {
    const updateData = { name: 'Updated' }
    const updatedProject = { ...mockProject, id: 999, ...updateData }
    
    vi.mocked(projectsApi.updateProject).mockResolvedValue({ data: updatedProject } as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    await store.updateProject(999, updateData)

    expect(store.currentProject?.name).toBe('Test Project')
  })

  it('非匹配 ID 的删除不影响 currentProject', async () => {
    vi.mocked(projectsApi.deleteProject).mockResolvedValue(undefined as any)

    const store = useProjectsStore()
    store.currentProject = mockProject
    
    await store.deleteProject(999)

    expect(store.currentProject).not.toBeNull()
  })
})
