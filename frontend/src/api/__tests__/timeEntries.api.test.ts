import { describe, it, expect, beforeEach, vi } from 'vitest'
import { timeEntriesApi } from '../timeEntries'
import apiClient from '../client'

vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Time Entries API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getTimeEntries 应发送正确的 GET 请求', async () => {
    const mockResponse = {
      data: [
        { id: 1, hours: 8, description: 'Development work' },
        { id: 2, hours: 4, description: 'Meeting' }
      ]
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getTimeEntries()

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  it('getTimeEntries 应带过滤参数发送请求', async () => {
    const params = {
      skip: 0,
      limit: 10,
      task_id: 1,
      user_id: 1,
      from_date: '2024-01-01',
      to_date: '2024-12-31'
    }

    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    await timeEntriesApi.getTimeEntries(params)

    expect(apiClient.get).toHaveBeenCalledWith('/time-entries', { params })
  })

  it('getTimeEntry 应发送正确的 GET 请求', async () => {
    const entryId = 1
    const mockResponse = {
      data: { id: 1, hours: 8, description: 'Development work', task_id: 1 }
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getTimeEntry(entryId)

    expect(apiClient.get).toHaveBeenCalledWith(`/time-entries/${entryId}`)
    expect(result).toEqual(mockResponse)
  })

  it('createTimeEntry 应发送正确的 POST 请求', async () => {
    const entryData = {
      task_id: 1,
      hours: 8,
      description: 'Development work',
      date: '2024-01-15'
    }

    const mockResponse = {
      data: { id: 1, ...entryData }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.createTimeEntry(entryData)

    expect(apiClient.post).toHaveBeenCalledWith('/time-entries', entryData)
    expect(result).toEqual(mockResponse)
  })

  it('updateTimeEntry 应发送正确的 PUT 请求', async () => {
    const entryId = 1
    const updateData = {
      hours: 6,
      description: 'Updated description'
    }

    const mockResponse = {
      data: { id: 1, ...updateData }
    }

    vi.mocked(apiClient.put).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.updateTimeEntry(entryId, updateData)

    expect(apiClient.put).toHaveBeenCalledWith(`/time-entries/${entryId}`, updateData)
    expect(result).toEqual(mockResponse)
  })

  it('deleteTimeEntry 应发送正确的 DELETE 请求', async () => {
    const entryId = 1

    vi.mocked(apiClient.delete).mockResolvedValue({ status: 204 })

    const result = await timeEntriesApi.deleteTimeEntry(entryId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/time-entries/${entryId}`)
    expect(result).toEqual({ status: 204 })
  })

  it('getTimeEntry 记录不存在时应抛出异常', async () => {
    const mockError = new Error('Time entry not found')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(timeEntriesApi.getTimeEntry(999)).rejects.toThrow('Time entry not found')
  })

  it('createTimeEntry 工时无效时应抛出异常', async () => {
    const mockError = new Error('Hours must be greater than 0')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      timeEntriesApi.createTimeEntry({ task_id: 1, hours: 0, date: '2024-01-01' } as any)
    ).rejects.toThrow('Hours must be greater than 0')
  })

  it('updateTimeEntry 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.put).mockRejectedValue(mockError)

    await expect(
      timeEntriesApi.updateTimeEntry(1, { hours: 8 })
    ).rejects.toThrow('Not enough permissions')
  })

  it('deleteTimeEntry 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.delete).mockRejectedValue(mockError)

    await expect(timeEntriesApi.deleteTimeEntry(1)).rejects.toThrow('Not enough permissions')
  })

  it('createTimeEntry 任务不存在时应抛出异常', async () => {
    const mockError = new Error('Task not found')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      timeEntriesApi.createTimeEntry({ task_id: 999, hours: 8, date: '2024-01-01' } as any)
    ).rejects.toThrow('Task not found')
  })

  it('getTimeEntries 网络错误应抛出异常', async () => {
    const mockError = new Error('Network Error')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(timeEntriesApi.getTimeEntries()).rejects.toThrow('Network Error')
  })

  it('getTimeEntries 应处理空列表返回', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await timeEntriesApi.getTimeEntries()

    expect(result.data).toHaveLength(0)
  })

  it('createTimeEntry 工时超过24小时应抛出异常', async () => {
    const mockError = new Error('Hours cannot exceed 24 per day')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    await expect(
      timeEntriesApi.createTimeEntry({ task_id: 1, hours: 25, date: '2024-01-01' } as any)
    ).rejects.toThrow('Hours cannot exceed 24 per day')
  })
})
