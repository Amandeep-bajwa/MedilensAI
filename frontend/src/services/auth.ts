import { api } from './api'

export interface UserSummary {
  user_id: string
  name: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserSummary
}

export interface UserProfileResponse extends UserSummary {
  updated_at: string
  total_reports: number
  total_medications: number
  total_appointments: number
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
  role?: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface ChangePasswordPayload {
  current_password: string
  new_password: string
}

export const authService = {
  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>('/auth/register', payload)
    localStorage.setItem('medilens_token', res.data.access_token)
    localStorage.setItem('medilens_user', JSON.stringify(res.data.user))
    return res.data
  },

  async login(payload: LoginPayload): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>('/auth/login', payload)
    localStorage.setItem('medilens_token', res.data.access_token)
    localStorage.setItem('medilens_user', JSON.stringify(res.data.user))
    return res.data
  },

  async getMe(): Promise<UserSummary> {
    const res = await api.get<UserSummary>('/auth/me')
    localStorage.setItem('medilens_user', JSON.stringify(res.data))
    return res.data
  },

  async getProfile(): Promise<UserProfileResponse> {
    const res = await api.get<UserProfileResponse>('/users/profile')
    return res.data
  },

  async updateProfile(name: string): Promise<UserSummary> {
    const res = await api.put<UserSummary>('/users/profile', { name })
    localStorage.setItem('medilens_user', JSON.stringify(res.data))
    return res.data
  },

  async changePassword(payload: ChangePasswordPayload): Promise<{ message: string }> {
    const res = await api.post<{ message: string }>('/auth/change-password', payload)
    return res.data
  },

  async deleteAccount(): Promise<void> {
    await api.delete('/users/profile')
    this.logout()
  },

  logout(): void {
    localStorage.removeItem('medilens_token')
    localStorage.removeItem('medilens_user')
  },

  getStoredUser(): UserSummary | null {
    const raw = localStorage.getItem('medilens_user')
    if (!raw) return null
    try {
      return JSON.parse(raw) as UserSummary
    } catch {
      return null
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('medilens_token')
  }
}
