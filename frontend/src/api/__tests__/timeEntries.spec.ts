import { describe, it, expect, vi, beforeEach } from 'vitest'
import { timeEntriesApi } from '../timeEntries'
import apiClient from '../client'
import type { TimeEntryCreate, TimeEntryUpdate } from '@/types'

// Mock apiClient
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('TimeEntries API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * 测试场景：正常获取工时记录列表
   * 验证：GET请求被正确发送到/time-entries
   */
  it('should call getTimeEntries endpoint', async () => {
    const mockResponse = {
      data: [
        {
          id: 1,
          task_id: 1,
          task: { id: 1, title: 'Task 1' },
          user_id: 1,
          user: { id: 1, username: 'user1' },
          hours: 8,
          date: '2024-01-15',
          description: 'Worked on feature',
          created_at: '2024-01-15T00:00:00Z'
        }
      ]
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getTimeEntries()

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：带参数获取工时记录列表
   * 验证：查询参数被正确传递
   */
  it('should call getTimeEntries with query params', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const params = {
      task_id: 1,
      user_id: 1,
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    }

    await timeEntriesApi.getTimeEntries(params)

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries', { params })
  })

  /**
   * 测试场景：获取工时记录列表失败
   * 验证：错误被正确抛出
   */
  it('should throw error when getTimeEntries fails', async () => {
    const error = new Error('Network error')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(timeEntriesApi.getTimeEntries()).rejects.toThrow('Network error')
  })

  /**
   * 测试场景：正常获取单个工时记录
   * 验证：GET请求被正确发送到/time-entries/{id}
   */
  it('should call getTimeEntry endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        task_id: 1,
        task: { id: 1, title: 'Task 1' },
        user_id: 1,
        user: { id: 1, username: 'user1' },
        hours: 8,
        date: '2024-01-15',
        description: 'Worked on feature',
        created_at: '2024-01-15T00:00:00Z'
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getTimeEntry(1)

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：获取不存在的工时记录
   * 验证：错误被正确抛出
   */
  it('should throw error when time entry not found', async () => {
    const error = new Error('Time entry not found')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(timeEntriesApi.getTimeEntry(999)).rejects.toThrow('Time entry not found')
  })

  /**
   * 测试场景：正常创建工时记录
   * 验证：POST请求被正确发送到/time-entries
   */
  it('should call createTimeEntry endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        task_id: 1,
        task: { id: 1, title: 'Task 1' },
        user_id: 1,
        user: { id: 1, username: 'user1' },
        hours: 8,
        date: '2024-01-15',
        description: 'Worked on feature',
        created_at: '2024-01-15T00:00:00Z'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const entryData: TimeEntryCreate = {
      task_id: 1,
      hours: 8,
      date: '2024-01-15',
      description: 'Worked on feature'
    }

    const result = await timeEntriesApi.createTimeEntry(entryData)

    expect(apiClient.post).toHaveBeenCalledWith('/time-entries', entryData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：创建工时记录失败（任务不存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when createTimeEntry task not found', async () => {
    const error = new Error('Task not found')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const entryData: TimeEntryCreate = {
      task_id: 999,
      hours: 8,
      date: '2024-01-15'
    }

    await expect(timeEntriesApi.createTimeEntry(entryData)).rejects.toThrow('Task not found')
  })

  /**
   * 测试场景：创建工时记录失败（工时无效）
   * 验证：错误被正确抛出
   */
  it('should throw error when createTimeEntry with invalid hours', async () => {
    const error = new Error('Hours must be greater than 0')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const entryData: TimeEntryCreate = {
      task_id: 1,
      hours: -1,
      date: '2024-01-15'
    }

    await expect(timeEntriesApi.createTimeEntry(entryData)).rejects.toThrow('Hours must be greater than 0')
  })

  /**
   * 测试场景：正常更新工时记录
   * 验证：PUT请求被正确发送到/time-entries/{id}
   */
  it('should call updateTimeEntry endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        task_id: 1,
        task: { id: 1, title: 'Task 1' },
        user_id: 1,
        user: { id: 1, username: 'user1' },
        hours: 6,
        date: '2024-01-15',
        description: 'Updated description',
        created_at: '2024-01-15T00:00:00Z'
      }
    }
    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const updateData: TimeEntryUpdate = {
      hours: 6,
      description: 'Updated description'
    }

    const result = await timeEntriesApi.updateTimeEntry(1, updateData)

    expect(apiClient.put).toHaveBeenCalledWith('/time-entries/1', updateData)
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：更新工时记录失败（权限不足）
   * 验证：错误被正确抛出
   */
  it('should throw error when updateTimeEntry permission denied', async () => {
    const error = new Error('Permission denied')
    vi.mocked(apiClient.put).mockRejectedValue(error)

    await expect(timeEntriesApi.updateTimeEntry(1, { hours: 5 })).rejects.toThrow('Permission denied')
  })

  /**
   * 测试场景：正常删除工时记录
   * 验证：DELETE请求被正确发送到/time-entries/{id}
   */
  it('should call deleteTimeEntry endpoint', async () => {
    const mockResponse = { data: undefined }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.deleteTimeEntry(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/time-entries/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：删除工时记录失败
   * 验证：错误被正确抛出
   */
  it('should throw error when deleteTimeEntry fails', async () => {
    const error = new Error('Time entry not found')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(timeEntriesApi.deleteTimeEntry(999)).rejects.toThrow('Time entry not found')
  })

  /**
   * 测试场景：正常获取工时统计
   * 验证：GET请求被正确发送到/time-entries/summary
   */
  it('should call getSummary endpoint', async () => {
    const mockResponse = {
      data: {
        total_hours: 40,
        daily_breakdown: [
          { date: '2024-01-15', hours: 8, entry_count: 1 },
          { date: '2024-01-16', hours: 8, entry_count: 1 }
        ]
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getSummary()

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries/summary', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：带参数获取工时统计
   * 验证：查询参数被正确传递
   */
  it('should call getSummary with query params', async () => {
    const mockResponse = {
      data: {
        total_hours: 20,
        daily_breakdown: []
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const params = {
      user_id: 1,
      project_id: 1,
      start_date: '2024-01-01',
      end_date: '2024-01-31'
    }

    await timeEntriesApi.getSummary(params)

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries/summary', { params })
  })

  /**
   * 测试场景：获取工时统计失败
   * 验证：错误被正确抛出
   */
  it('should throw error when getSummary fails', async () => {
    const error = new Error('Failed to get summary')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(timeEntriesApi.getSummary()).rejects.toThrow('Failed to get summary')
  })
})
