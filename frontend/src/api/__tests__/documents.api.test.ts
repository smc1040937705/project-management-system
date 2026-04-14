import { describe, it, expect, beforeEach, vi } from 'vitest'
import { documentsApi } from '../documents'
import apiClient from '../client'

vi.mock('../client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Documents API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('getDocuments 应发送正确的 GET 请求', async () => {
    const mockResponse = {
      data: [
        { id: 1, name: 'document.pdf', file_size: 1024 },
        { id: 2, name: 'report.docx', file_size: 2048 }
      ]
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.getDocuments()

    expect(apiClient.get).toHaveBeenCalledWith('/documents', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  it('getDocuments 应带过滤参数发送请求', async () => {
    const params = {
      skip: 0,
      limit: 10,
      project_id: 1,
      search: 'report'
    }

    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    await documentsApi.getDocuments(params)

    expect(apiClient.get).toHaveBeenCalledWith('/documents', { params })
  })

  it('getDocument 应发送正确的 GET 请求', async () => {
    const docId = 1
    const mockResponse = {
      data: { id: 1, name: 'document.pdf', file_size: 1024, project_id: 1 }
    }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.getDocument(docId)

    expect(apiClient.get).toHaveBeenCalledWith(`/documents/${docId}`)
    expect(result).toEqual(mockResponse)
  })

  it('uploadDocument 应发送正确的 POST 请求', async () => {
    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const formData = {
      project_id: 1,
      file: mockFile,
      description: 'Test document'
    }

    const mockResponse = {
      data: { id: 1, name: 'test.pdf', file_size: 1024 }
    }

    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const result = await documentsApi.uploadDocument(formData as any)

    expect(apiClient.post).toHaveBeenCalledWith(
      '/documents',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    )
    expect(result).toEqual(mockResponse)
  })

  it('deleteDocument 应发送正确的 DELETE 请求', async () => {
    const docId = 1

    vi.mocked(apiClient.delete).mockResolvedValue({ status: 204 })

    const result = await documentsApi.deleteDocument(docId)

    expect(apiClient.delete).toHaveBeenCalledWith(`/documents/${docId}`)
    expect(result).toEqual({ status: 204 })
  })

  it('downloadDocument 应发送正确的 GET 请求', async () => {
    const docId = 1
    const mockBlob = new Blob(['content'], { type: 'application/pdf' })
    const mockResponse = { data: mockBlob }

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.downloadDocument(docId)

    expect(apiClient.get).toHaveBeenCalledWith(`/documents/${docId}/download`, {
      responseType: 'blob'
    })
    expect(result).toEqual(mockResponse)
  })

  it('getDocument 文档不存在时应抛出异常', async () => {
    const mockError = new Error('Document not found')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(documentsApi.getDocument(999)).rejects.toThrow('Document not found')
  })

  it('uploadDocument 文件过大时应抛出异常', async () => {
    const mockError = new Error('File size exceeds maximum limit')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    const mockFile = new File(['large content'], 'large.pdf', { type: 'application/pdf' })
    await expect(
      documentsApi.uploadDocument({ project_id: 1, file: mockFile } as any)
    ).rejects.toThrow('File size exceeds maximum limit')
  })

  it('uploadDocument 不支持的文件类型应抛出异常', async () => {
    const mockError = new Error('Unsupported file type')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    const mockFile = new File(['content'], 'test.exe', { type: 'application/exe' })
    await expect(
      documentsApi.uploadDocument({ project_id: 1, file: mockFile } as any)
    ).rejects.toThrow('Unsupported file type')
  })

  it('deleteDocument 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.delete).mockRejectedValue(mockError)

    await expect(documentsApi.deleteDocument(1)).rejects.toThrow('Not enough permissions')
  })

  it('downloadDocument 网络错误应抛出异常', async () => {
    const mockError = new Error('Network Error')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(documentsApi.downloadDocument(1)).rejects.toThrow('Network Error')
  })

  it('getDocuments 应处理空列表返回', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.getDocuments()

    expect(result.data).toHaveLength(0)
  })

  it('uploadDocument 项目不存在时应抛出异常', async () => {
    const mockError = new Error('Project not found')
    vi.mocked(apiClient.post).mockRejectedValue(mockError)

    const mockFile = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    await expect(
      documentsApi.uploadDocument({ project_id: 999, file: mockFile } as any)
    ).rejects.toThrow('Project not found')
  })

  it('getDocuments 权限不足时应抛出异常', async () => {
    const mockError = new Error('Not enough permissions')
    vi.mocked(apiClient.get).mockRejectedValue(mockError)

    await expect(documentsApi.getDocuments()).rejects.toThrow('Not enough permissions')
  })
})
