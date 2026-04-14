import { describe, it, expect, vi, beforeEach } from 'vitest'
import { documentsApi } from '../documents'
import apiClient from '../client'

// Mock apiClient
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Documents API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * 测试场景：正常获取文档列表
   * 验证：GET请求被正确发送到/documents
   */
  it('should call getDocuments endpoint', async () => {
    const mockResponse = {
      data: [
        {
          id: 1,
          project_id: 1,
          name: 'document.pdf',
          file_path: '/uploads/documents/uuid_document.pdf',
          file_size: 1024,
          mime_type: 'application/pdf',
          uploaded_by: 1,
          uploader: { id: 1, username: 'user1' },
          version: 1,
          created_at: '2024-01-15T00:00:00Z'
        }
      ]
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.getDocuments()

    expect(apiClient.get).toHaveBeenCalledWith('/documents', { params: undefined })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：带参数获取文档列表
   * 验证：查询参数被正确传递
   */
  it('should call getDocuments with query params', async () => {
    const mockResponse = { data: [] }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const params = {
      project_id: 1,
      search: 'report'
    }

    await documentsApi.getDocuments(params)

    expect(apiClient.get).toHaveBeenCalledWith('/documents', { params })
  })

  /**
   * 测试场景：获取文档列表失败
   * 验证：错误被正确抛出
   */
  it('should throw error when getDocuments fails', async () => {
    const error = new Error('Network error')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(documentsApi.getDocuments()).rejects.toThrow('Network error')
  })

  /**
   * 测试场景：正常获取单个文档
   * 验证：GET请求被正确发送到/documents/{id}
   */
  it('should call getDocument endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        project_id: 1,
        name: 'document.pdf',
        file_path: '/uploads/documents/uuid_document.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
        uploaded_by: 1,
        uploader: { id: 1, username: 'user1' },
        version: 1,
        created_at: '2024-01-15T00:00:00Z'
      }
    }
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

    const result = await documentsApi.getDocument(1)

    expect(apiClient.get).toHaveBeenCalledWith('/documents/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：获取不存在的文档
   * 验证：错误被正确抛出
   */
  it('should throw error when document not found', async () => {
    const error = new Error('Document not found')
    vi.mocked(apiClient.get).mockRejectedValue(error)

    await expect(documentsApi.getDocument(999)).rejects.toThrow('Document not found')
  })

  /**
   * 测试场景：正常上传文档
   * 验证：POST请求被正确发送，使用FormData
   */
  it('should call uploadDocument endpoint', async () => {
    const mockResponse = {
      data: {
        id: 1,
        project_id: 1,
        name: 'test.pdf',
        file_path: '/uploads/documents/uuid_test.pdf',
        file_size: 1024,
        mime_type: 'application/pdf',
        uploaded_by: 1,
        uploader: { id: 1, username: 'user1' },
        version: 1,
        created_at: '2024-01-15T00:00:00Z'
      }
    }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

    const result = await documentsApi.uploadDocument(1, file, 'test.pdf', 'Description')

    expect(apiClient.post).toHaveBeenCalled()
    const callArgs = vi.mocked(apiClient.post).mock.calls[0]
    expect(callArgs[0]).toBe('/documents/upload?project_id=1')
    expect(callArgs[1]).toBeInstanceOf(FormData)
    expect(callArgs[2]).toEqual({
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：上传文档（不带可选参数）
   * 验证：FormData只包含必要字段
   */
  it('should upload document without optional params', async () => {
    const mockResponse = { data: { id: 1 } }
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

    await documentsApi.uploadDocument(1, file)

    const callArgs = vi.mocked(apiClient.post).mock.calls[0]
    const formData = callArgs[1] as FormData
    expect(formData.has('file')).toBe(true)
    expect(formData.has('project_id')).toBe(true)
  })

  /**
   * 测试场景：上传文档失败（文件类型不支持）
   * 验证：错误被正确抛出
   */
  it('should throw error when uploadDocument file type not allowed', async () => {
    const error = new Error('File type not allowed')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const file = new File(['content'], 'test.exe', { type: 'application/x-msdownload' })

    await expect(documentsApi.uploadDocument(1, file)).rejects.toThrow('File type not allowed')
  })

  /**
   * 测试场景：上传文档失败（文件过大）
   * 验证：错误被正确抛出
   */
  it('should throw error when uploadDocument file too large', async () => {
    const error = new Error('File size exceeds maximum allowed size')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const largeContent = new Array(11 * 1024 * 1024).fill('a').join('')
    const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' })

    await expect(documentsApi.uploadDocument(1, file)).rejects.toThrow('File size exceeds maximum allowed size')
  })

  /**
   * 测试场景：上传文档失败（项目不存在）
   * 验证：错误被正确抛出
   */
  it('should throw error when uploadDocument project not found', async () => {
    const error = new Error('Project not found')
    vi.mocked(apiClient.post).mockRejectedValue(error)

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })

    await expect(documentsApi.uploadDocument(999, file)).rejects.toThrow('Project not found')
  })

  /**
   * 测试场景：正常删除文档
   * 验证：DELETE请求被正确发送到/documents/{id}
   */
  it('should call deleteDocument endpoint', async () => {
    const mockResponse = { data: undefined }
    vi.mocked(apiClient.delete).mockResolvedValue(mockResponse)

    const result = await documentsApi.deleteDocument(1)

    expect(apiClient.delete).toHaveBeenCalledWith('/documents/1')
    expect(result).toEqual(mockResponse)
  })

  /**
   * 测试场景：删除文档失败（权限不足）
   * 验证：错误被正确抛出
   */
  it('should throw error when deleteDocument permission denied', async () => {
    const error = new Error('Permission denied')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(documentsApi.deleteDocument(1)).rejects.toThrow('Permission denied')
  })

  /**
   * 测试场景：删除不存在的文档
   * 验证：错误被正确抛出
   */
  it('should throw error when deleteDocument document not found', async () => {
    const error = new Error('Document not found')
    vi.mocked(apiClient.delete).mockRejectedValue(error)

    await expect(documentsApi.deleteDocument(999)).rejects.toThrow('Document not found')
  })
})
