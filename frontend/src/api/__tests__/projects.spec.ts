import { describe, it, expect, vi, beforeEach } from 'vitest'
import { projectsApi } from '../projects'
import apiClient from '../client'
import type { ProjectCreate, ProjectUpdate } from '@/types'

// Mock apiClient
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Projects API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * 测试场景：正常获取项目列表
   * 验证：GET请求被正确发送到/projects
   */
  it('should call getProjects endpoint', async () => {
    const mockResponse = {
      data: [
        {
          id: 1,
          name: 'Project 1',
          status: 'active',
          owner_id: 1,
          members: [],
          created_at: '2024-01-01T00:00:00Z',
          task_count: 0,
          completed_task_count: 0
        }
      ]
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await projectsApi.getProjects()

    expect(apiClient.get).toHaveBeenCalledWith('/projects', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：带参数获取项目列表
   * 验证：查询参数被正确传递
   */
  it('should call getProjects with query params', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const params = {
      skip: 0,
      limit: 20,
      status: 'active',
      search: 'test'
    }

    await projectsApi.getProjects(params)

    expect(apiClient.get).toHaveBeenCalledWith('/projects', { params })
  })

  /**
   * 测试场景：获取项目列表失败
   * 验证：错误被正确抛出
   */
  it('should throw error when getProjects fails', async () => {
    const error = new Error('Network error')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(projectsApi.getProjects()).rejects.toThrow('Network error')
  })

  /**
   * 测试场景：正常获取单个项目
   * 验证：GET请求被正确发送到/projects/{id}
   */
  it('should call getProject endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        name: 'Project 1',
        status: 'active',
        owner_id: 1,
        members: [],
        created_at: '2024-01-01T00:00:00Z',
        task_count: 0,
        completed_task_count: 0
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await projectsApi.getProject(1)

    expect(apiClient.get).toHaveBeenCalledWith('/projects/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：获取不存在的项目
   * 验证：错误被正确抛出
   */
  it('should throw error when project not found', async () => {
    const error = new Error('Project not found')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(projectsApi.getProject(999)).rejects.toThrow('Project not found')
  })

  /**
   * 测试场景：正常创建项目
   * 验证：POST请求被正确发送到/projects
   */
  it('should call createProject endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        name: 'New Project',
        status: 'planning',
        owner_id: 1,
        members: [],
        created_at: '2024-01-01T00:00:00Z',
        task_count: 0,
        completed_task_count: 0
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const projectData: ProjectCreate = {
      name: 'New Project',
      description: 'Description',
      status: 'planning',
      member_ids: [1, 2]
    }

    const result = await projectsApi.createProject(projectData)

    expect(apiClient.post).toHaveBeenCalledWith('/projects', projectData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：创建项目失败（验证错误）
   * 验证：错误被正确抛出
   */
  it('should throw error when createProject validation fails', async () => {
    const error = new Error('Name is required')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const projectData: ProjectCreate = {
      name: '',
      status: 'planning'
    }

    await expect(projectsApi.createProject(projectData)).rejects.toThrow('Name is required')
  })

  /**
   * 测试场景：正常更新项目
   * 验证：PUT请求被正确发送到/projects/{id}
   */
  it('should call updateProject endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        name: 'Updated Project',
        status: 'active',
        owner_id: 1,
        members: [],
        created_at: '2024-01-01T00:00:00Z',
        task_count: 0,
        completed_task_count: 0
      }
    }
    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const updateData: ProjectUpdate = {
      name: 'Updated Project',
      status: 'active'
    }

    const result = await projectsApi.updateProject(1, updateData)

    expect(apiClient.put).toHaveBeenCalledWith('/projects/1', updateData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：更新项目失败（权限不足）
   * 验证：错误被正确抛出
   */
  it('should throw error when updateProject permission denied', async () => {
    const error = new Error('Permission denied')
    vi.mocked(apiClient.put).mockRejectedValue(error)

    await expect(projectsApi.updateProject(1, { name: 'New' })).rejects.toThrow('Permission denied')
  })

  /**
   * 测试场景：正常删除项目
   * 验证：DELETE请求被正确发送到/projects/{id}
   */
  it('should call deleteProject endpoint', async () => {
    const mockResponse = { data: undefined }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await projectsApi.deleteProject(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/projects/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：删除项目失败
   * 验证：错误被正确抛出
   */
  it('should throw error when deleteProject fails', async () => {
    const error = new Error('Project not found')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(projectsApi.deleteProject(999)).rejects.toThrow('Project not found')
  })

  /**
   * 测试场景：正常添加项目成员
   * 验证：POST请求被正确发送
   */
  it('should call addMember endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        name: 'Project 1',
        members: [{ id: 2, email: 'member@example.com', username: 'member', first_name: 'Member', last_name: 'User', role: 'member', is_active: true, created_at: '2024-01-01T00:00:00Z' }],
        status: 'active',
        owner_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        task_count: 0,
        completed_task_count: 0
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await projectsApi.addMember(1, 2)

    expect(apiClient.post).toHaveBeenCalledWith('/projects/1/members/2')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：添加成员失败（用户不存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when addMember user not found', async () => {
    const error = new Error('User not found')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    await expect(projectsApi.addMember(1, 999)).rejects.toThrow('User not found')
  })

  /**
   * 测试场景：正常移除项目成员
   * 验证：DELETE请求被正确发送
   */
  it('should call removeMember endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        name: 'Project 1',
        members: [],
        status: 'active',
        owner_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        task_count: 0,
        completed_task_count: 0
      }
    }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await projectsApi.removeMember(1, 2)

    expect(apiClient.delete).toHaveBeenCalledWith('/projects/1/members/2')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：移除成员失败
   * 验证：错误被正确抛出
   */
  it('should throw error when removeMember fails', async () => {
    const error = new Error('Member not found in project')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(projectsApi.removeMember(1, 999)).rejects.toThrow('Member not found in project')
  })
})
