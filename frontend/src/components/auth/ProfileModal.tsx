import React, { useState, useEffect } from 'react'
import { X, User, KeyRound, LogOut, Check, AlertCircle, FileText, Pill, Calendar, Loader2 } from 'lucide-react'
import { authService, type UserSummary, type UserProfileResponse } from '../../services/auth'

interface ProfileModalProps {
  isOpen: boolean
  onClose: () => void
  user: UserSummary
  onLogout: () => void
  onUserUpdated: (user: UserSummary) => void
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  onClose,
  user,
  onLogout,
  onUserUpdated
}) => {
  const [profile, setProfile] = useState<UserProfileResponse | null>(null)
  const [loadingProfile, setLoadingProfile] = useState<boolean>(true)
  const [editingName, setEditingName] = useState<boolean>(false)
  const [newName, setNewName] = useState<string>(user.name)

  // Password change states
  const [showPasswordChange, setShowPasswordChange] = useState<boolean>(false)
  const [currentPassword, setCurrentPassword] = useState<string>('')
  const [newPassword, setNewPassword] = useState<string>('')
  const [passwordStatus, setPasswordStatus] = useState<{ success?: string; error?: string } | null>(null)
  const [changingPassword, setChangingPassword] = useState<boolean>(false)

  useEffect(() => {
    if (isOpen) {
      loadProfile()
    }
  }, [isOpen])

  const loadProfile = async () => {
    setLoadingProfile(true)
    try {
      const data = await authService.getProfile()
      setProfile(data)
      setNewName(data.name)
    } catch {
      // Fallback
    } finally {
      setLoadingProfile(false)
    }
  }

  if (!isOpen) return null

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    try {
      const updated = await authService.updateProfile(newName.trim())
      onUserUpdated(updated)
      setEditingName(false)
    } catch {
      // Handle error
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordStatus(null)
    setChangingPassword(true)

    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword
      })
      setPasswordStatus({ success: 'Password successfully changed!' })
      setCurrentPassword('')
      setNewPassword('')
      setTimeout(() => setShowPasswordChange(false), 2000)
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Failed to update password.'
      setPasswordStatus({ error: msg })
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-center space-x-4 mb-6">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white font-bold text-xl">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white">{user.name}</h2>
              <span className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${
                user.role === 'admin'
                  ? 'bg-rose-950/80 text-rose-400 border-rose-800'
                  : 'bg-cyan-950/80 text-cyan-400 border-cyan-800'
              }`}>
                {user.role.toUpperCase()}
              </span>
            </div>
            <p className="text-xs text-slate-400">{user.email}</p>
          </div>
        </div>

        {/* Live Metrics */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-center">
            <FileText className="h-4 w-4 mx-auto text-cyan-400 mb-1" />
            <div className="text-lg font-bold text-white">
              {loadingProfile ? '-' : profile?.total_reports ?? 0}
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Reports</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-center">
            <Pill className="h-4 w-4 mx-auto text-amber-400 mb-1" />
            <div className="text-lg font-bold text-white">
              {loadingProfile ? '-' : profile?.total_medications ?? 0}
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Medications</div>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-center">
            <Calendar className="h-4 w-4 mx-auto text-emerald-400 mb-1" />
            <div className="text-lg font-bold text-white">
              {loadingProfile ? '-' : profile?.total_appointments ?? 0}
            </div>
            <div className="text-[10px] text-slate-400 uppercase tracking-wider">Appointments</div>
          </div>
        </div>

        {/* Edit Name */}
        {editingName ? (
          <form onSubmit={handleUpdateName} className="mb-4 flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-white focus:outline-none focus:border-cyan-500"
            />
            <button
              type="submit"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-500"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => setEditingName(false)}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700"
            >
              Cancel
            </button>
          </form>
        ) : (
          <button
            onClick={() => setEditingName(true)}
            className="w-full mb-3 flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-2.5 text-xs font-medium text-slate-300 hover:border-slate-700 transition"
          >
            <span className="flex items-center gap-2">
              <User className="h-4 w-4 text-slate-400" /> Edit Profile Name
            </span>
            <span className="text-cyan-400">Edit</span>
          </button>
        )}

        {/* Change Password Toggle */}
        <button
          onClick={() => setShowPasswordChange(!showPasswordChange)}
          className="w-full mb-4 flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-2.5 text-xs font-medium text-slate-300 hover:border-slate-700 transition"
        >
          <span className="flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-slate-400" /> Security &amp; Password
          </span>
          <span className="text-cyan-400">{showPasswordChange ? 'Hide' : 'Change'}</span>
        </button>

        {/* Password Change Form */}
        {showPasswordChange && (
          <form onSubmit={handleChangePassword} className="mb-4 p-4 rounded-xl border border-slate-800 bg-slate-950/60 space-y-3">
            {passwordStatus?.success && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 p-2 rounded-lg">
                <Check className="h-4 w-4" /> {passwordStatus.success}
              </div>
            )}
            {passwordStatus?.error && (
              <div className="flex items-center gap-2 text-xs text-rose-400 bg-rose-950/40 border border-rose-800/40 p-2 rounded-lg">
                <AlertCircle className="h-4 w-4" /> {passwordStatus.error}
              </div>
            )}
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">Current Password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-[11px] text-slate-400 mb-1">New Password (min 8 chars)</label>
              <input
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              disabled={changingPassword}
              className="w-full flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-50"
            >
              {changingPassword ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Update Password'}
            </button>
          </form>
        )}

        {/* Logout Button */}
        <button
          onClick={() => {
            onLogout()
            onClose()
          }}
          className="w-full flex items-center justify-center gap-2 rounded-xl border border-rose-900/50 bg-rose-950/20 py-2.5 text-xs font-semibold text-rose-400 hover:bg-rose-950/40 transition"
        >
          <LogOut className="h-4 w-4" /> Sign Out
        </button>
      </div>
    </div>
  )
}
