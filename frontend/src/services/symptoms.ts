import { api } from './api'

export interface RedFlagAlert {
  symptom: string
  urgency_reason: string
  action_required: string
}

export interface SymptomAnalyzeRequest {
  symptoms: string
  duration?: string
  severity?: number
  additional_notes?: string
}

export interface SymptomAnalysisResponse {
  interaction_id: string
  symptoms: string
  triage_level: 'EMERGENCY' | 'URGENT' | 'ROUTINE'
  is_emergency: boolean
  red_flags: RedFlagAlert[]
  recommended_specialist: string
  clinical_assessment: string
  possible_causes: string[]
  supportive_care_tips: string[]
  doctor_questions: string[]
  disclaimer: string
  created_at: string
}

export interface SymptomHistoryItem {
  interaction_id: string
  symptoms: string
  triage_level: string
  recommended_specialist: string
  summary_text: string
  created_at: string
}

export interface CommonSymptomCategory {
  category: string
  symptoms: string[]
}

export const symptomsService = {
  async analyzeSymptoms(request: SymptomAnalyzeRequest): Promise<SymptomAnalysisResponse> {
    const res = await api.post<SymptomAnalysisResponse>('/symptoms/analyze', request)
    return res.data
  },

  async getHistory(): Promise<SymptomHistoryItem[]> {
    const res = await api.get<SymptomHistoryItem[]>('/symptoms/history')
    return res.data
  },

  async getCommonSymptoms(): Promise<CommonSymptomCategory[]> {
    const res = await api.get<CommonSymptomCategory[]>('/symptoms/common')
    return res.data
  }
}
