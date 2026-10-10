import { api } from './api'

export interface RAGCitation {
  chunk_id: string
  page_number: string
  snippet: string
  relevance_score: number
}

export interface RAGQueryRequest {
  question: string
  top_k?: number
}

export interface RAGQueryResponse {
  query_id: string
  report_id: string
  question: string
  answer: string
  citations: RAGCitation[]
  confidence_score: number
  is_grounded: boolean
  disclaimer: string
  created_at: string
}

export interface RAGIndexStatusResponse {
  report_id: string
  total_chunks: number
  indexed_chunks: number
  status: string
  algorithm: string
  last_indexed_at?: string
}

export interface RAGReindexResponse {
  report_id: string
  indexed_count: number
  message: string
}

export interface RAGHistoryItem {
  interaction_id: string
  question: string
  response: string
  created_at: string
}

export const ragService = {
  async queryRAG(
    reportId: string,
    question: string,
    topK: number = 3
  ): Promise<RAGQueryResponse> {
    const res = await api.post<RAGQueryResponse>(`/reports/${reportId}/rag/query`, {
      question,
      top_k: topK
    })
    return res.data
  },

  async getIndexStatus(reportId: string): Promise<RAGIndexStatusResponse> {
    const res = await api.get<RAGIndexStatusResponse>(`/reports/${reportId}/rag/status`)
    return res.data
  },

  async reindexChunks(reportId: string): Promise<RAGReindexResponse> {
    const res = await api.post<RAGReindexResponse>(`/reports/${reportId}/rag/reindex`)
    return res.data
  },

  async getHistory(reportId: string): Promise<RAGHistoryItem[]> {
    const res = await api.get<RAGHistoryItem[]>(`/reports/${reportId}/rag/history`)
    return res.data
  }
}
