import { api } from './api'

export interface LabParameter {
  name: string
  value: string
  unit?: string
  reference_range?: string
  status: 'NORMAL' | 'HIGH' | 'LOW' | 'UNKNOWN'
}

export interface ReportChunkItem {
  chunk_id: string
  report_id: string
  chunk_text: string
  page_number?: string
  embedding_reference?: string
  created_at: string
}

export interface OCRData {
  ocr_id: string
  report_id: string
  extracted_text: string
  confidence: number
  status: string
  parameters: LabParameter[]
  total_chunks: number
  created_at: string
}

export interface ChunksListResponse {
  report_id: string
  total_chunks: number
  chunks: ReportChunkItem[]
}

export const ocrService = {
  async processOCR(reportId: string): Promise<OCRData> {
    const res = await api.post<OCRData>(`/reports/${reportId}/ocr/process`)
    return res.data
  },

  async getOCRData(reportId: string): Promise<OCRData> {
    const res = await api.get<OCRData>(`/reports/${reportId}/ocr`)
    return res.data
  },

  async getChunks(reportId: string): Promise<ChunksListResponse> {
    const res = await api.get<ChunksListResponse>(`/reports/${reportId}/chunks`)
    return res.data
  }
}
