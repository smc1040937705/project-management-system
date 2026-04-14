import apiClient from './client'
import type { Document, DocumentCreate } from '@/types'

export const documentsApi = {
  getDocuments: (params?: { skip?: number; limit?: number; project_id?: number; search?: string }) =>
    apiClient.get<Document[]>('/documents', { params }),

  getDocument: (id: number) =>
    apiClient.get<Document>(`/documents/${id}`),

  uploadDocument: (data: DocumentCreate) => {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('project_id', data.project_id.toString())
    if (data.description) formData.append('description', data.description)
    return apiClient.post<Document>('/documents', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  deleteDocument: (id: number) =>
    apiClient.delete(`/documents/${id}`),

  downloadDocument: (id: number) =>
    apiClient.get<Blob>(`/documents/${id}/download`, {
      responseType: 'blob'
    })
}
