import { api } from './api'

export interface Notification {
  notification_id: string
  user_id: string
  title: string
  message: string
  type: 'REPORT_PROCESSED' | 'MEDICATION_REMINDER' | 'APPOINTMENT_REMINDER' | 'SYSTEM' | string
  is_read: boolean
  link: string | null
  created_at: string
}

export interface NotificationCreatePayload {
  title: string
  message: string
  type?: string
  link?: string | null
}

export interface NotificationListResponse {
  total: number
  unread_count: number
  items: Notification[]
}

export interface RemindersGenerationResponse {
  generated_count: number
  details: string[]
}

export const notificationsService = {
  listNotifications: async (unreadOnly = false): Promise<NotificationListResponse> => {
    const res = await api.get<NotificationListResponse>('/notifications', {
      params: { unread_only: unreadOnly }
    })
    return res.data
  },

  createNotification: async (payload: NotificationCreatePayload): Promise<Notification> => {
    const res = await api.post<Notification>('/notifications', payload)
    return res.data
  },

  markAsRead: async (notificationId: string): Promise<Notification> => {
    const res = await api.patch<Notification>(`/notifications/${notificationId}/read`)
    return res.data
  },

  markAllAsRead: async (): Promise<{ message: string; updated_count: number }> => {
    const res = await api.post<{ message: string; updated_count: number }>('/notifications/mark-all-read')
    return res.data
  },

  deleteNotification: async (notificationId: string): Promise<void> => {
    await api.delete(`/notifications/${notificationId}`)
  },

  generateReminders: async (): Promise<RemindersGenerationResponse> => {
    const res = await api.post<RemindersGenerationResponse>('/notifications/generate-reminders')
    return res.data
  }
}
