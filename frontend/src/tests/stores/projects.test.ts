import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useProjectsStore } from '@/stores/projects'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types'

const mockUser = {
  id: 1,
  email: 'owner@example.com',
  username: 'owner',
  first_name: 'Owner',
  last_name: 'User',
  role: 'admin' as const,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
}

const mockProjects: Project[] = [
  {
    id: 1,
    name: 'Project 1',
    description: 'Description 1',
    status: 'active',
    owner_id: 1,
    owner: mockUser,
    members: [],
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    budget: 10000,
    created_at: '2024-01-01T00:00:00Z',
    task_count: 5,
    completed_task_count: 2,
  },
  {
    id: 2,
    name: 'Project 2',
    description: 'Description 2',
    status: 'planning',
    owner_id: 1,
    owner: mockUser,
    members: [],
    created_at: '2024-01-02T00:00:00Z',
    task_count: 0,
    completed_task_count: 0,
  },
]

vi.mock('@/api', () => ({
  projectsApi: {
    getProjects: vi.fn(),
    getProject: vi.fn(),
    createProject: vi.fn(),
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    addMember: vi.fn(),
    removeMember: vi.fn(),
  },
}))

import { projectsApi } from '@/api'

describe('useProjectsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('初始状态应该是空的', () => {
      const store = useProjectsStore()
      
      expect(store.projects).toEqual([])
      expect(store.currentProject).toBeNull()
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })
  })

  describe('fetchProjects', () => {
    it('获取项目列表成功', async () => {
      const store = useProjectsStore()
      
      vi.mocked(projectsApi.getProjects).mockResolvedValue({
        data: mockProjects,
      } as any)

      const result = await store.fetchProjects()

      expect(projectsApi.getProjects).toHaveBeenCalledWith(undefined)
      expect(store.projects).toEqual(mockProjects)
      expect(store.loading).toBe(false)
      expect(result).toEqual(mockProjects)
    })

    it('带参数获取项目列表', async () => {
      const store = useProjectsStore()
      
      vi.mocked(projectsApi.getProjects).mockResolvedValue({
        data: [mockProjects[0]],
      } as any)

      const params = { status: 'active', search: 'Project 1' }
      const result = await store.fetchProjects(params)

      expect(projectsApi.getProjects).toHaveBeenCalledWith(params)
      expect(store.projects).toHaveLength(1)
      expect(result).toHaveLength(1)
    })

    it('获取项目列表失败应设置错误信息', async () => {
      const store = useProjectsStore()
      
      const error = new Error('Network error')
      vi.mocked(projectsApi.getProjects).mockRejectedValue(error)

      await expect(store.fetchProjects()).rejects.toThrow('Network error')
      expect(store.error).toBe('Network error')
      expect(store.loading).toBe(false)
    })
  })

  describe('fetchProject', () => {
    it('获取单个项目成功', async () => {
      const store = useProjectsStore()
      
      vi.mocked(projectsApi.getProject).mockResolvedValue({
        data: mockProjects[0],
      } as any)

      const result = await store.fetchProject(1)

      expect(projectsApi.getProject).toHaveBeenCalledWith(1)
      expect(store.currentProject).toEqual(mockProjects[0])
      expect(result).toEqual(mockProjects[0])
    })

    it('获取不存在的项目应抛出错误', async () => {
      const store = useProjectsStore()
      
      const error = new Error('Project not found')
      vi.mocked(projectsApi.getProject).mockRejectedValue(error)

      await expect(store.fetchProject(999)).rejects.toThrow('Project not found')
      expect(store.error).toBe('Project not found')
    })
  })

  describe('createProject', () => {
    it('创建项目成功', async () => {
      const store = useProjectsStore()
      const newProjectData: ProjectCreate = {
        name: 'New Project',
        description: 'New Description',
        status: 'planning',
      }

      const createdProject: Project = {
        id: 3,
        ...newProjectData,
        owner_id: 1,
        owner: mockUser,
        members: [],
        created_at: '2024-01-03T00:00:00Z',
        task_count: 0,
        completed_task_count: 0,
      }

      vi.mocked(projectsApi.createProject).mockResolvedValue({
        data: createdProject,
      } as any)

      const result = await store.createProject(newProjectData)

      expect(projectsApi.createProject).toHaveBeenCalledWith(newProjectData)
      expect(store.projects).toContainEqual(createdProject)
      expect(result).toEqual(createdProject)
    })

    it('创建项目失败应抛出错误', async () => {
      const store = useProjectsStore()
      const newProjectData: ProjectCreate = {
        name: '',
        status: 'planning',
      }

      const error = new Error('Validation error')
      vi.mocked(projectsApi.createProject).mockRejectedValue(error)

      await expect(store.createProject(newProjectData)).rejects.toThrow('Validation error')
      expect(store.error).toBe('Validation error')
    })
  })

  describe('updateProject', () => {
    it('更新项目成功', async () => {
      const store = useProjectsStore()
      store.projects = [...mockProjects]
      
      const updateData: ProjectUpdate = {
        name: 'Updated Project 1',
        status: 'completed',
      }

      const updatedProject: Project = {
        ...mockProjects[0],
        ...updateData,
      }

      vi.mocked(projectsApi.updateProject).mockResolvedValue({
        data: updatedProject,
      } as any)

      const result = await store.updateProject(1, updateData)

      expect(projectsApi.updateProject).toHaveBeenCalledWith(1, updateData)
      expect(store.projects[0]).toEqual(updatedProject)
      expect(result).toEqual(updatedProject)
    })

    it('更新当前项目时应同步更新currentProject', async () => {
      const store = useProjectsStore()
      store.projects = [...mockProjects]
      store.currentProject = mockProjects[0]
      
      const updateData: ProjectUpdate = {
        status: 'completed',
      }

      const updatedProject: Project = {
        ...mockProjects[0],
        status: 'completed',
      }

      vi.mocked(projectsApi.updateProject).mockResolvedValue({
        data: updatedProject,
      } as any)

      await store.updateProject(1, updateData)

      expect(store.currentProject).toEqual(updatedProject)
    })

    it('更新不存在的项目应抛出错误', async () => {
      const store = useProjectsStore()
      
      const error = new Error('Project not found')
      vi.mocked(projectsApi.updateProject).mockRejectedValue(error)

      await expect(store.updateProject(999, { name: 'Test' })).rejects.toThrow('Project not found')
    })
  })

  describe('deleteProject', () => {
    it('删除项目成功', async () => {
      const store = useProjectsStore()
      store.projects = [...mockProjects]
      
      vi.mocked(projectsApi.deleteProject).mockResolvedValue({} as any)

      await store.deleteProject(1)

      expect(projectsApi.deleteProject).toHaveBeenCalledWith(1)
      expect(store.projects.find(p => p.id === 1)).toBeUndefined()
      expect(store.projects).toHaveLength(1)
    })

    it('删除当前项目时应清除currentProject', async () => {
      const store = useProjectsStore()
      store.projects = [...mockProjects]
      store.currentProject = mockProjects[0]
      
      vi.mocked(projectsApi.deleteProject).mockResolvedValue({} as any)

      await store.deleteProject(1)

      expect(store.currentProject).toBeNull()
    })

    it('删除不存在的项目应抛出错误', async () => {
      const store = useProjectsStore()
      
      const error = new Error('Project not found')
      vi.mocked(projectsApi.deleteProject).mockRejectedValue(error)

      await expect(store.deleteProject(999)).rejects.toThrow('Project not found')
    })
  })

  describe('addMember', () => {
    it('添加成员成功', async () => {
      const store = useProjectsStore()
      store.currentProject = mockProjects[0]
      
      const updatedProject: Project = {
        ...mockProjects[0],
        members: [{ ...mockUser, id: 2 }],
      }

      vi.mocked(projectsApi.addMember).mockResolvedValue({
        data: updatedProject,
      } as any)

      const result = await store.addMember(1, 2)

      expect(projectsApi.addMember).toHaveBeenCalledWith(1, 2)
      expect(store.currentProject).toEqual(updatedProject)
      expect(result).toEqual(updatedProject)
    })

    it('添加成员到非当前项目不应更新currentProject', async () => {
      const store = useProjectsStore()
      store.currentProject = mockProjects[0]
      
      const updatedProject: Project = {
        ...mockProjects[1],
        members: [{ ...mockUser, id: 2 }],
      }

      vi.mocked(projectsApi.addMember).mockResolvedValue({
        data: updatedProject,
      } as any)

      await store.addMember(2, 2)

      expect(store.currentProject).toEqual(mockProjects[0])
    })
  })

  describe('removeMember', () => {
    it('移除成员成功', async () => {
      const projectWithMember: Project = {
        ...mockProjects[0],
        members: [{ ...mockUser, id: 2 }],
      }
      const store = useProjectsStore()
      store.currentProject = projectWithMember
      
      const updatedProject: Project = {
        ...mockProjects[0],
        members: [],
      }

      vi.mocked(projectsApi.removeMember).mockResolvedValue({
        data: updatedProject,
      } as any)

      await store.removeMember(1, 2)

      expect(projectsApi.removeMember).toHaveBeenCalledWith(1, 2)
      expect(store.currentProject).toEqual(updatedProject)
    })
  })

  describe('loading状态', () => {
    it('操作过程中应正确设置loading状态', async () => {
      const store = useProjectsStore()
      
      vi.mocked(projectsApi.getProjects).mockImplementation(() => {
        expect(store.loading).toBe(true)
        return Promise.resolve({ data: mockProjects } as any)
      })

      const promise = store.fetchProjects()
      expect(store.loading).toBe(true)
      
      await promise
      expect(store.loading).toBe(false)
    })
  })
})
