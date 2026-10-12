import React, { useState, useEffect, useRef } from 'react'
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  FileText,
  Pill,
  Calendar,
  Info,
  RotateCw,
  X,
  Loader2
} from 'lucide-react'
import {
  notificationsService,
  type Notification
} from '../../services/notifications'

interface NotificationBellDropdownProps {
  onNotificationClick?: (link: string | null) => void
  onRemindersGenerated?: () => void
}

export const NotificationBellDropdown: React.FC<NotificationBellDropdownProps> = ({
  onNotificationClick,
  onRemindersGenerated
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [syncingReminders, setSyncingReminders] = useState(false)
  const [filterUnread, setFilterUnread] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const loadNotifications = async () => {
    try {
      setLoading(true)
      const res = await notificationsService.listNotifications(filterUnread)
      setNotifications(res.items)
      setUnreadCount(res.unread_count)
    } catch {
      // Handled silently
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadNotifications()
    const interval = setInterval(loadNotifications, 30000)
    return () => clearInterval(interval)
  }, [filterUnread])

  // Handle outside click to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [isOpen])

  const handleMarkAsRead = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await notificationsService.markAsRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === id ? { ...n, is_read: true } : n))
      )
      setUnreadCount((c) => Math.max(0, c - 1))
    } catch {
      // Ignore
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await notificationsService.markAllAsRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // Ignore
    }
  }

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await notificationsService.deleteNotification(id)
      setNotifications((prev) => prev.filter((n) => n.notification_id !== id))
      loadNotifications()
    } catch {
      // Ignore
    }
  }

  const handleSyncReminders = async () => {
    try {
      setSyncingReminders(true)
      await notificationsService.generateReminders()
      await loadNotifications()
      if (onRemindersGenerated) onRemindersGenerated()
    } finally {
      setSyncingReminders(false)
    }
  }

  const getIconForType = (type: string) => {
    switch (type) {
      case 'REPORT_PROCESSED':
        return <FileText className="h-4 w-4 text-cyan-400" />
      case 'MEDICATION_REMINDER':
        return <Pill className="h-4 w-4 text-emerald-400" />
      case 'APPOINTMENT_REMINDER':
        return <Calendar className="h-4 w-4 text-amber-400" />
      default:
        return <Info className="h-4 w-4 text-purple-400" />
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition cursor-pointer"
        title="Notifications & Health Alerts"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white shadow-sm animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Popover Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-84 sm:w-96 rounded-xl border border-slate-800 bg-slate-900/95 backdrop-blur-md shadow-2xl z-50 text-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
            <div className="flex items-center space-x-2">
              <span className="font-semibold text-xs text-white">Alerts & Notifications</span>
              {unreadCount > 0 && (
                <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded-full bg-rose-950 border border-rose-800 text-rose-300">
                  {unreadCount} new
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleSyncReminders}
                disabled={syncingReminders}
                className="text-slate-400 hover:text-cyan-400 transition p-1 cursor-pointer"
                title="Sync medication & appointment reminders"
              >
                <RotateCw className={`h-3.5 w-3.5 ${syncingReminders ? 'animate-spin text-cyan-400' : ''}`} />
              </button>
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition cursor-pointer"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  <span>Mark Read</span>
                </button>
              )}
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-500 hover:text-slate-300 p-0.5"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="px-4 py-2 border-b border-slate-800/60 bg-slate-950/30 flex items-center justify-between text-[11px] text-slate-400">
            <span>Filter:</span>
            <div className="flex space-x-2">
              <button
                onClick={() => setFilterUnread(false)}
                className={`px-2 py-0.5 rounded transition ${
                  !filterUnread ? 'bg-slate-800 text-white font-medium' : 'hover:text-slate-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilterUnread(true)}
                className={`px-2 py-0.5 rounded transition ${
                  filterUnread ? 'bg-slate-800 text-white font-medium' : 'hover:text-slate-200'
                }`}
              >
                Unread Only
              </button>
            </div>
          </div>

          {/* Notification Items List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-800/40">
            {loading && notifications.length === 0 ? (
              <div className="py-8 flex flex-col items-center justify-center text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin text-cyan-400 mb-1" />
                <span className="text-xs">Loading alerts...</span>
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center text-slate-400">
                <Bell className="h-8 w-8 text-slate-600 mx-auto mb-2 opacity-50" />
                <p className="text-xs font-medium text-slate-300">No notifications</p>
                <p className="text-[11px] text-slate-500 mt-0.5">You're all caught up with your clinical updates.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.notification_id}
                  onClick={() => {
                    if (!n.is_read) handleMarkAsRead(n.notification_id, {} as React.MouseEvent)
                    if (onNotificationClick && n.link) onNotificationClick(n.link)
                  }}
                  className={`p-3.5 hover:bg-slate-800/60 transition cursor-pointer flex items-start gap-3 ${
                    !n.is_read ? 'bg-slate-950/40' : 'opacity-80'
                  }`}
                >
                  <div className="p-2 rounded-lg bg-slate-800/80 shrink-0 mt-0.5 border border-slate-700/50">
                    {getIconForType(n.type)}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p className={`text-xs font-medium truncate ${!n.is_read ? 'text-white' : 'text-slate-300'}`}>
                        {n.title}
                      </p>
                      {!n.is_read && (
                        <span className="h-2 w-2 rounded-full bg-cyan-400 shrink-0 inline-block" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                      {n.message}
                    </p>
                    <span className="text-[10px] text-slate-500 block mt-1">
                      {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {new Date(n.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex flex-col items-center gap-1 shrink-0">
                    {!n.is_read && (
                      <button
                        onClick={(e) => handleMarkAsRead(n.notification_id, e)}
                        className="text-slate-500 hover:text-cyan-400 p-1 transition"
                        title="Mark as read"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDelete(n.notification_id, e)}
                      className="text-slate-500 hover:text-rose-400 p-1 transition"
                      title="Delete notification"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
