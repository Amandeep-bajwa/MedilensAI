import React, { useState, useEffect } from 'react'
import {
  Activity,
  FileText,
  Pill,
  Calendar,
  Sparkles,
  Stethoscope,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  UploadCloud,
  ChevronRight,
  User,
  ShieldCheck,
  Loader2
} from 'lucide-react'
import {
  dashboardService,
  type DashboardSummaryResponse
} from '../../services/dashboard'

interface DashboardViewProps {
  onNavigateToReports: () => void
  onOpenHealthTracker: () => void
  onOpenSymptomTriage: () => void
  onOpenUpload: () => void
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigateToReports,
  onOpenHealthTracker,
  onOpenSymptomTriage,
  onOpenUpload
}) => {
  const [summary, setSummary] = useState<DashboardSummaryResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await dashboardService.getSummary()
      setSummary(data)
    } catch {
      setError('Unable to fetch dashboard metrics. Please ensure backend is running.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [])

  if (loading) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-slate-400 space-y-3">
        <Loader2 className="h-10 w-10 animate-spin text-cyan-500" />
        <p className="text-sm font-medium text-slate-300">Loading your clinical health dashboard...</p>
      </div>
    )
  }

  if (error || !summary) {
    return (
      <div className="p-6 rounded-xl border border-rose-800/60 bg-rose-950/20 text-center max-w-lg mx-auto my-12">
        <AlertCircle className="h-10 w-10 text-rose-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-rose-200">Dashboard Unavailable</h3>
        <p className="text-xs text-rose-300/80 mt-1">{error || 'Failed to aggregate data.'}</p>
        <button
          onClick={loadDashboardData}
          className="mt-4 px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-white transition cursor-pointer"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Clinical Health Dashboard
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400">
              Phase 9
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Holistic overview of medical reports, active prescriptions, physician follow-ups, and AI diagnostic insights.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={loadDashboardData}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 text-xs font-medium transition cursor-pointer"
            title="Refresh statistics"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <button
            onClick={onOpenUpload}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition cursor-pointer"
          >
            <UploadCloud className="h-3.5 w-3.5" />
            <span>Upload Report</span>
          </button>

          <button
            onClick={onOpenSymptomTriage}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-amber-800/60 bg-amber-950/40 text-amber-300 hover:bg-amber-900/60 transition text-xs font-semibold cursor-pointer"
          >
            <Stethoscope className="h-3.5 w-3.5" />
            <span>Symptom Triage</span>
          </button>
        </div>
      </div>

      {/* 4 Stat Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Total Reports */}
        <div
          onClick={onNavigateToReports}
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-cyan-500/50 hover:bg-slate-900 transition cursor-pointer flex flex-col justify-between group shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Reports</span>
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold tracking-tight text-white">{summary.total_reports}</div>
            <div className="flex items-center gap-2 mt-2 text-[11px] text-slate-400">
              <span className="text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" />
                {summary.reports_by_status.Completed || 0} Ready
              </span>
              <span>&bull;</span>
              <span>{summary.reports_by_status.Processing || 0} Processing</span>
            </div>
          </div>
        </div>

        {/* Metric 2: Active Prescriptions */}
        <div
          onClick={onOpenHealthTracker}
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-emerald-500/50 hover:bg-slate-900 transition cursor-pointer flex flex-col justify-between group shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Regimens</span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-800/60 text-emerald-400">
              <Pill className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold tracking-tight text-white">{summary.active_medications_count}</div>
            <p className="mt-2 text-[11px] text-slate-400 flex items-center gap-1 group-hover:text-emerald-400 transition">
              <span>View prescriptions</span>
              <ChevronRight className="h-3 w-3" />
            </p>
          </div>
        </div>

        {/* Metric 3: Upcoming Consultations */}
        <div
          onClick={onOpenHealthTracker}
          className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-blue-500/50 hover:bg-slate-900 transition cursor-pointer flex flex-col justify-between group shadow-sm"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Upcoming Visits</span>
            <div className="p-2 rounded-lg bg-blue-950/60 border border-blue-800/60 text-blue-400">
              <Calendar className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold tracking-tight text-white">{summary.upcoming_appointments_count}</div>
            <p className="mt-2 text-[11px] text-slate-400 flex items-center gap-1 group-hover:text-blue-400 transition">
              <span>View appointment schedule</span>
              <ChevronRight className="h-3 w-3" />
            </p>
          </div>
        </div>

        {/* Metric 4: System Alerts */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 flex flex-col justify-between shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Unread Alerts</span>
            <div className="p-2 rounded-lg bg-purple-950/60 border border-purple-800/60 text-purple-400">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3">
            <div className="text-3xl font-bold tracking-tight text-white">{summary.unread_notifications_count}</div>
            <p className="mt-2 text-[11px] text-slate-400 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3 text-emerald-400" />
              <span>Adherence alerts active</span>
            </p>
          </div>
        </div>
      </div>

      {/* Main 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Recent Reports & AI Insights */}
        <div className="space-y-6">
          {/* Recent Reports Card */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-white">Recent Lab Reports</h2>
              </div>
              <button
                onClick={onNavigateToReports}
                className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 transition"
              >
                <span>All Reports</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            {summary.recent_reports.length === 0 ? (
              <div className="text-center py-8 text-slate-400 border border-dashed border-slate-800/60 rounded-xl">
                <p className="text-xs font-medium text-slate-300">No reports uploaded yet</p>
                <p className="text-[11px] text-slate-500 mt-1">Upload blood tests or diagnostic panels to begin.</p>
                <button
                  onClick={onOpenUpload}
                  className="mt-3 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
                >
                  Upload First Report
                </button>
              </div>
            ) : (
              <div className="space-y-2.5">
                {summary.recent_reports.map((report) => (
                  <div
                    key={report.report_id}
                    onClick={onNavigateToReports}
                    className="p-3 rounded-xl border border-slate-800/80 bg-slate-950/40 hover:border-slate-700 transition flex items-center justify-between cursor-pointer"
                  >
                    <div className="min-w-0 pr-3">
                      <p className="text-xs font-medium text-white truncate">{report.file_name}</p>
                      <div className="flex items-center space-x-2 mt-1 text-[11px] text-slate-400">
                        <span className="px-1.5 py-0.2 rounded bg-slate-900 border border-slate-800 text-slate-300 font-mono text-[10px]">
                          {report.category}
                        </span>
                        <span>&bull;</span>
                        <span>{new Date(report.uploaded_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full shrink-0 ${
                        report.processing_status === 'Completed'
                          ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                          : report.processing_status === 'Processing'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800/60 animate-pulse'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}
                    >
                      {report.processing_status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent AI Activity Card */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-800/60">
              <Sparkles className="h-4 w-4 text-purple-400" />
              <h2 className="text-sm font-semibold text-white">Recent AI Diagnostic Activity</h2>
            </div>

            {summary.recent_ai_activity.length === 0 ? (
              <div className="text-center py-6 text-slate-400 border border-dashed border-slate-800/60 rounded-xl">
                <p className="text-xs text-slate-400">No recent AI explanations or Q&A interactions.</p>
                <p className="text-[11px] text-slate-500 mt-1">Generate a summary or ask report questions to see logs.</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {summary.recent_ai_activity.map((act) => (
                  <div
                    key={act.id}
                    className="p-3 rounded-xl border border-slate-800/80 bg-slate-950/40 flex items-start gap-3"
                  >
                    <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 shrink-0 mt-0.5">
                      {act.activity_type === 'SYMPTOM_TRIAGE' ? (
                        <Stethoscope className="h-3.5 w-3.5 text-amber-400" />
                      ) : (
                        <Sparkles className="h-3.5 w-3.5 text-purple-400" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider">
                          {act.activity_type.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {new Date(act.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 mt-1 line-clamp-2">{act.summary}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Medications & Upcoming Appointments */}
        <div className="space-y-6">
          {/* Active Medications Card */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
              <div className="flex items-center space-x-2">
                <Pill className="h-4 w-4 text-emerald-400" />
                <h2 className="text-sm font-semibold text-white">Active Medication Regimens</h2>
              </div>
              <button
                onClick={onOpenHealthTracker}
                className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1 transition"
              >
                <span>Manage Regimens</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            {summary.active_medications.length === 0 ? (
              <div className="text-center py-8 text-slate-400 border border-dashed border-slate-800/60 rounded-xl">
                <p className="text-xs font-medium text-slate-300">No active prescriptions</p>
                <p className="text-[11px] text-slate-500 mt-1">Record dosages, frequencies, and duration courses.</p>
                <button
                  onClick={onOpenHealthTracker}
                  className="mt-3 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
                >
                  Add Prescription
                </button>
              </div>
            ) : (
              <div className="space-y-2.5">
                {summary.active_medications.map((med) => (
                  <div
                    key={med.medication_id}
                    className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-950/40 flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-white">{med.medicine_name}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 border border-emerald-800/60 text-emerald-400 font-medium">
                          {med.dosage}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Frequency: <span className="text-slate-300 font-medium">{med.frequency}</span>
                      </p>
                      <span className="text-[10px] text-slate-500 block mt-0.5">
                        Started: {med.start_date} {med.end_date ? `• Until: ${med.end_date}` : '• Ongoing'}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800/60">
                      Active
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming Appointments Card */}
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-blue-400" />
                <h2 className="text-sm font-semibold text-white">Upcoming Physician Appointments</h2>
              </div>
              <button
                onClick={onOpenHealthTracker}
                className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition"
              >
                <span>Book / Reschedule</span>
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>

            {summary.upcoming_appointments.length === 0 ? (
              <div className="text-center py-8 text-slate-400 border border-dashed border-slate-800/60 rounded-xl">
                <p className="text-xs font-medium text-slate-300">No consultations scheduled</p>
                <p className="text-[11px] text-slate-500 mt-1">Keep track of clinical checkups and specialist referrals.</p>
                <button
                  onClick={onOpenHealthTracker}
                  className="mt-3 px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition"
                >
                  Schedule Appointment
                </button>
              </div>
            ) : (
              <div className="space-y-2.5">
                {summary.upcoming_appointments.map((appt) => (
                  <div
                    key={appt.appointment_id}
                    className="p-3.5 rounded-xl border border-slate-800/80 bg-slate-950/40 flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-semibold text-white flex items-center gap-1">
                          <User className="h-3 w-3 text-blue-400" />
                          {appt.doctor_name}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-950/80 border border-blue-800/60 text-blue-300 font-medium">
                          {appt.specialization}
                        </span>
                      </div>
                      <div className="flex items-center space-x-3 mt-1 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1 text-slate-300">
                          <Clock className="h-3 w-3 text-slate-500" />
                          {appt.appointment_date} at {appt.appointment_time}
                        </span>
                        {appt.location && (
                          <span className="text-slate-400 truncate max-w-xs">&bull; {appt.location}</span>
                        )}
                      </div>
                    </div>

                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-950 text-amber-400 border border-amber-800/60 shrink-0">
                      Upcoming
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
