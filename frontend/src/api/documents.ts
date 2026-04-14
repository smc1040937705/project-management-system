import apiClient from './client'
import type { Document, DocumentCreate } from '@/types'

export const documentsApi = {
  getDocuments: (params?: { skip?: number; limit?: number; project_id?: number; search?: string }) =>
    apiClient.get<Document[]>('/documents', { params }),

  getDocument: (id: number) =>
    apiClient.get<Document>(`/documents/${id}`),

  uploadDocument: (projectId: number, file: File, name?: string, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('project_id', projectId.toString())
    if (name) formData.append('name', name)
    if (description) formData.append('description', description)
    return apiClient.post<Document>(`/documents/upload?project_id=${projectId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  deleteDocument: (id: number) =>
    apiClient.delete(`/documents/${id}`)
}
