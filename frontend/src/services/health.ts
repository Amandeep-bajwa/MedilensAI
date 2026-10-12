import { api } from './api'

export interface Medication {
  medication_id: string
  user_id: string
  medicine_name: string
  dosage: string
  frequency: string
  start_date: string
  end_date: string | null
  notes: string | null
  is_active: boolean
  created_at: string
}

export interface MedicationCreatePayload {
  medicine_name: string
  dosage: string
  frequency: string
  start_date: string
  end_date?: string | null
  notes?: string | null
}

export interface MedicationUpdatePayload {
  medicine_name?: string
  dosage?: string
  frequency?: string
  start_date?: string
  end_date?: string | null
  notes?: string | null
}

export interface MedicationListResponse {
  total: number
  items: Medication[]
}

export interface Appointment {
  appointment_id: string
  user_id: string
  doctor_name: string
  specialization: string
  appointment_date: string
  appointment_time: string
  location: string | null
  notes: string | null
  status: 'Upcoming' | 'Completed' | 'Cancelled' | string
  created_at: string
}

export interface AppointmentCreatePayload {
  doctor_name: string
  specialization: string
  appointment_date: string
  appointment_time: string
  location?: string | null
  notes?: string | null
  status?: string
}

export interface AppointmentUpdatePayload {
  doctor_name?: string
  specialization?: string
  appointment_date?: string
  appointment_time?: string
  location?: string | null
  notes?: string | null
  status?: string
}

export interface AppointmentListResponse {
  total: number
  items: Appointment[]
}

export const healthService = {
  // Medications
  listMedications: async (activeOnly = false): Promise<MedicationListResponse> => {
    const res = await api.get<MedicationListResponse>('/medications', {
      params: { active_only: activeOnly }
    })
    return res.data
  },

  createMedication: async (payload: MedicationCreatePayload): Promise<Medication> => {
    const res = await api.post<Medication>('/medications', payload)
    return res.data
  },

  updateMedication: async (id: string, payload: MedicationUpdatePayload): Promise<Medication> => {
    const res = await api.put<Medication>(`/medications/${id}`, payload)
    return res.data
  },

  deleteMedication: async (id: string): Promise<void> => {
    await api.delete(`/medications/${id}`)
  },

  // Appointments
  listAppointments: async (statusFilter?: string): Promise<AppointmentListResponse> => {
    const res = await api.get<AppointmentListResponse>('/appointments', {
      params: statusFilter ? { status: statusFilter } : {}
    })
    return res.data
  },

  createAppointment: async (payload: AppointmentCreatePayload): Promise<Appointment> => {
    const res = await api.post<Appointment>('/appointments', payload)
    return res.data
  },

  updateAppointment: async (id: string, payload: AppointmentUpdatePayload): Promise<Appointment> => {
    const res = await api.put<Appointment>(`/appointments/${id}`, payload)
    return res.data
  },

  deleteAppointment: async (id: string): Promise<void> => {
    await api.delete(`/appointments/${id}`)
  }
}
