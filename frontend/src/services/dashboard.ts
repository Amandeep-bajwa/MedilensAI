import { api } from './api'

export interface DashboardReportItem {
  report_id: string
  file_name: string
  file_type: string
  category: string
  processing_status: string
  uploaded_at: string
}

export interface DashboardMedicationItem {
  medication_id: string
  medicine_name: string
  dosage: string
  frequency: string
  start_date: string
  end_date: string | null
  is_active: boolean
}

export interface DashboardAppointmentItem {
  appointment_id: string
  doctor_name: string
  specialization: string
  appointment_date: string
  appointment_time: string
  location: string | null
  status: string
}

export interface DashboardAIActivityItem {
  id: string
  activity_type: 'REPORT_EXPLANATION' | 'RAG_QUESTION' | 'SYMPTOM_TRIAGE' | string
  summary: string
  timestamp: string
  reference_id: string | null
}

export interface DashboardSummaryResponse {
  total_reports: number
  reports_by_status: {
    Uploaded: number
    Processing: number
    Completed: number
    Failed: number
    [key: string]: number
  }
  active_medications_count: number
  upcoming_appointments_count: number
  unread_notifications_count: number
  recent_reports: DashboardReportItem[]
  active_medications: DashboardMedicationItem[]
  upcoming_appointments: DashboardAppointmentItem[]
  recent_ai_activity: DashboardAIActivityItem[]
}

export const dashboardService = {
  getSummary: async (): Promise<DashboardSummaryResponse> => {
    const res = await api.get<DashboardSummaryResponse>('/dashboard/summary')
    return res.data
  }
}
