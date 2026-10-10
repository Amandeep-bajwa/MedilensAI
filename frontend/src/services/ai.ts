import { api } from './api'

export interface AbnormalFindingItem {
  parameter_name: string
  observed_value: string
  reference_interval: string
  flag: string
  plain_english_explanation: string
}

export interface ReportExplanationResponse {
  interaction_id: string
  report_id: string
  summary: string
  key_findings: string[]
  abnormal_findings: AbnormalFindingItem[]
  lifestyle_recommendations: string[]
  doctor_questions: string[]
  disclaimer: string
  provider_used: string
  created_at: string
}

export interface AskReportQuestionRequest {
  question: string
}

export interface AskReportQuestionResponse {
  interaction_id: string
  report_id: string
  question: string
  answer: string
  disclaimer: string
  created_at: string
}

export interface AIInteractionSummary {
  interaction_id: string
  report_id?: string
  question: string
  response: string
  created_at: string
}

export const aiService = {
  async explainReport(
    reportId: string,
    focusAreas?: string,
    language: string = 'en'
  ): Promise<ReportExplanationResponse> {
    const res = await api.post<ReportExplanationResponse>(`/reports/${reportId}/explain`, {
      focus_areas: focusAreas || null,
      language
    })
    return res.data
  },

  async getExplanation(reportId: string): Promise<ReportExplanationResponse> {
    const res = await api.get<ReportExplanationResponse>(`/reports/${reportId}/explanation`)
    return res.data
  },

  async askQuestion(reportId: string, question: string): Promise<AskReportQuestionResponse> {
    const res = await api.post<AskReportQuestionResponse>(`/reports/${reportId}/ask`, {
      question
    })
    return res.data
  },

  async getInteractions(reportId: string): Promise<AIInteractionSummary[]> {
    const res = await api.get<AIInteractionSummary[]>(`/reports/${reportId}/interactions`)
    return res.data
  }
}
