import { api } from './api'

export interface ReportItem {
  report_id: string
  user_id: string
  file_name: string
  file_type: string
  category: string
  processing_status: string
  file_size_bytes?: number
  uploaded_at: string
  updated_at: string
}

export interface ReportListResponse {
  items: ReportItem[]
  total: number
  page: number
  limit: number
}

export const reportsService = {
  async uploadReport(file: File, category: string = 'Other'): Promise<ReportItem> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('category', category)

    const res = await api.post<ReportItem>('/reports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return res.data
  },

  async listReports(params?: {
    skip?: number
    limit?: number
    category?: string
    processing_status?: string
    search?: string
  }): Promise<ReportListResponse> {
    const res = await api.get<ReportListResponse>('/reports/', { params })
    return res.data
  },

  async getReport(reportId: string): Promise<ReportItem> {
    const res = await api.get<ReportItem>(`/reports/${reportId}`)
    return res.data
  },

  async downloadReport(reportId: string, fileName: string): Promise<void> {
    const res = await api.get(`/reports/${reportId}/download`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },

  async updateReport(reportId: string, category: string): Promise<ReportItem> {
    const res = await api.patch<ReportItem>(`/reports/${reportId}`, { category })
    return res.data
  },

  async deleteReport(reportId: string): Promise<void> {
    await api.delete(`/reports/${reportId}`)
  }
}
