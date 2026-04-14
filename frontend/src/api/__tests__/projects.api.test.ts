import { describe, it, expect, beforeEach, vi } from 'vitest'
import { projectsApi } from '../projects'
import apiClient from '../client'

vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Projects API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getProjects 应发送正确的 GET 请求', async () => {
    const mockResponse = {
      data: [
        { id: 1, name: 'Project 1' },
        { id: 2, name: 'Project 2' }
      ]
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await projectsApi.getProjects()

    expect(apiClient.get).toHaveBeenCalledWith('/projects', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  it('getProjects 应带参数发送请求', async () => {
    const params = {
      skip: 0,
      limit: 10,
      status: 'active',
      search: 'test'
    }

    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    await projectsApi.getProjects(params)

    expect(apiClient.get).toHaveBeenCalledWith('/projects', { params })
  })

  it('getProject 应发送正确的 GET 请求', async () => {
    const projectId = 1
    const mockResponse = {
      data: { id: 1, name: 'Test Project' }
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await projectsApi.getProject(projectId)

    expect(apiClient.get).toHaveBeenCalledWith(`/projects/${projectId}`)
    expect(result).toEqual(mockResponse)
  })

  it('createProject 应发送正确的 POST 请求', async () => {
    const projectData = {
      name: 'New Project',
      description: 'Description',
      status: 'active',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      budget: 10000,
      member_ids: [1, 2]
    }

    const mockResponse = {
      data: { id: 1, ...projectData }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await projectsApi.createProject(projectData)

    expect(apiClient.post).toHaveBeenCalledWith('/projects', projectData)
    expect(result).toEqual(mockResponse)
  })

  it('updateProject 应发送正确的 PUT 请求', async () => {
    const projectId = 1
    const updateData = {
      name: 'Updated Project',
      description: 'Updated Description'
    }

    const mockResponse = {
      data: { id: 1, ...updateData }
    }

    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const result = await projectsApi.updateProject(projectId, updateData)

    expect(apiClient.put).toHaveBeenCalledWith(`/projects/${projectId}`, updateData)
    expect(result).toEqual(mockResponse)
  })

  it('deleteProject 应发送正确的 DELETE 请求', async () => {
    const projectId = 1

    vi.mocked(apiClient.delete).mockResolvedValue({ status: 204 })

    const result = await projectsApi.deleteProject(projectId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/projects/${projectId}`)
    expect(result).toEqual({ status: 204 })
  })

  it('addMember 应发送正确的 POST 请求', async () => {
    const projectId = 1
    const userId = 2

    const mockResponse = {
      data: { id: 1, members: [{ id: 2 }] }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await projectsApi.addMember(projectId, userId)

    expect(apiClient.post).toHaveBeenCalledWith(`/projects/${projectId}/members/${userId}`)
    expect(result).toEqual(mockResponse)
  })

  it('removeMember 应发送正确的 DELETE 请求', async () => {
    const projectId = 1
    const userId = 2

    const mockResponse = {
      data: { id: 1, members: [] }
    }

    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await projectsApi.removeMember(projectId, userId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/projects/${projectId}/members/${userId}`)
    expect(result).toEqual(mockResponse)
  })

  it('getProject 项目不存在时应抛出异常', async () => {
    const mockError = new Error('Project not found')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(projectsApi.getProject(999)).rejects.toThrow('Project not found')
  })

  it('deleteProject 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.delete).mockRejectedValue(mockError)

    await expect(projectsApi.deleteProject(1)).rejects.toThrow('Not enough permissions')
  })
})
