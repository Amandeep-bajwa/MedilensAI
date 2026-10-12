import React, { useState, useEffect } from 'react'
import {
  X,
  Pill,
  Calendar,
  Clock,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  MapPin,
  User,
  Stethoscope,
  Filter,
  Loader2,
  CalendarCheck2
} from 'lucide-react'
import {
  healthService,
  type Medication,
  type Appointment,
  type MedicationCreatePayload,
  type AppointmentCreatePayload
} from '../../services/health'

interface HealthTrackerModalProps {
  isOpen: boolean
  onClose: () => void
}

export const HealthTrackerModal: React.FC<HealthTrackerModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'medications' | 'appointments'>('medications')

  // Medications state
  const [medications, setMedications] = useState<Medication[]>([])
  const [loadingMeds, setLoadingMeds] = useState(false)
  const [activeOnlyFilter, setActiveOnlyFilter] = useState(false)
  const [showAddMedModal, setShowAddMedModal] = useState(false)
  const [medForm, setMedForm] = useState<MedicationCreatePayload>({
    medicine_name: '',
    dosage: '',
    frequency: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: ''
  })
  const [submittingMed, setSubmittingMed] = useState(false)

  // Appointments state
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loadingAppts, setLoadingAppts] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showAddApptModal, setShowAddApptModal] = useState(false)
  const [apptForm, setApptForm] = useState<AppointmentCreatePayload>({
    doctor_name: '',
    specialization: 'General Physician',
    appointment_date: new Date().toISOString().split('T')[0],
    appointment_time: '10:00 AM',
    location: '',
    notes: '',
    status: 'Upcoming'
  })
  const [submittingAppt, setSubmittingAppt] = useState(false)

  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  const showNotification = (message: string, type: 'success' | 'error') => {
    setFeedback({ message, type })
    setTimeout(() => setFeedback(null), 4000)
  }

  // Load Medications
  const loadMedications = async () => {
    setLoadingMeds(true)
    try {
      const res = await healthService.listMedications(activeOnlyFilter)
      setMedications(res.items)
    } catch {
      showNotification('Unable to load medications schedule.', 'error')
    } finally {
      setLoadingMeds(false)
    }
  }

  // Load Appointments
  const loadAppointments = async () => {
    setLoadingAppts(true)
    try {
      const res = await healthService.listAppointments(statusFilter || undefined)
      setAppointments(res.items)
    } catch {
      showNotification('Unable to load appointment schedule.', 'error')
    } finally {
      setLoadingAppts(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      if (activeTab === 'medications') {
        loadMedications()
      } else {
        loadAppointments()
      }
    }
  }, [isOpen, activeTab, activeOnlyFilter, statusFilter])

  // Handlers for Medications
  const handleAddMedication = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!medForm.medicine_name.trim() || !medForm.dosage.trim() || !medForm.frequency.trim()) {
      showNotification('Please fill in all mandatory medication fields.', 'error')
      return
    }

    setSubmittingMed(true)
    try {
      await healthService.createMedication({
        medicine_name: medForm.medicine_name.trim(),
        dosage: medForm.dosage.trim(),
        frequency: medForm.frequency.trim(),
        start_date: medForm.start_date,
        end_date: medForm.end_date ? medForm.end_date : null,
        notes: medForm.notes?.trim() || null
      })
      showNotification('Prescription added successfully.', 'success')
      setShowAddMedModal(false)
      setMedForm({
        medicine_name: '',
        dosage: '',
        frequency: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        notes: ''
      })
      loadMedications()
    } catch {
      showNotification('Failed to create medication record.', 'error')
    } finally {
      setSubmittingMed(false)
    }
  }

  const handleDeleteMedication = async (medicationId: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name} from your medications?`)) return
    try {
      await healthService.deleteMedication(medicationId)
      showNotification(`${name} removed successfully.`, 'success')
      loadMedications()
    } catch {
      showNotification('Failed to delete medication.', 'error')
    }
  }

  // Handlers for Appointments
  const handleAddAppointment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!apptForm.doctor_name.trim() || !apptForm.specialization.trim() || !apptForm.appointment_time.trim()) {
      showNotification('Please fill in doctor name, specialization, and time.', 'error')
      return
    }

    setSubmittingAppt(true)
    try {
      await healthService.createAppointment({
        doctor_name: apptForm.doctor_name.trim(),
        specialization: apptForm.specialization.trim(),
        appointment_date: apptForm.appointment_date,
        appointment_time: apptForm.appointment_time.trim(),
        location: apptForm.location?.trim() || null,
        notes: apptForm.notes?.trim() || null,
        status: apptForm.status || 'Upcoming'
      })
      showNotification('Appointment scheduled successfully.', 'success')
      setShowAddApptModal(false)
      setApptForm({
        doctor_name: '',
        specialization: 'General Physician',
        appointment_date: new Date().toISOString().split('T')[0],
        appointment_time: '10:00 AM',
        location: '',
        notes: '',
        status: 'Upcoming'
      })
      loadAppointments()
    } catch {
      showNotification('Failed to schedule appointment.', 'error')
    } finally {
      setSubmittingAppt(false)
    }
  }

  const handleUpdateApptStatus = async (apptId: string, newStatus: string) => {
    try {
      await healthService.updateAppointment(apptId, { status: newStatus })
      showNotification(`Appointment marked as ${newStatus}.`, 'success')
      loadAppointments()
    } catch {
      showNotification('Failed to update appointment status.', 'error')
    }
  }

  const handleDeleteAppointment = async (apptId: string) => {
    if (!confirm('Are you sure you want to remove this appointment record?')) return
    try {
      await healthService.deleteAppointment(apptId)
      showNotification('Appointment record deleted.', 'success')
      loadAppointments()
    } catch {
      showNotification('Failed to delete appointment record.', 'error')
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-100">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-md shadow-blue-500/20 text-white">
              <CalendarCheck2 className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold tracking-tight text-white flex items-center gap-2">
                Health Tracker & Regimens
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-950 border border-blue-800 text-blue-400">
                  Phase 8
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Manage your prescribed medications, dosages, and physician consultations
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {/* Tab Buttons */}
            <div className="flex bg-slate-950 rounded-lg p-1 border border-slate-800 text-xs font-medium">
              <button
                onClick={() => setActiveTab('medications')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
                  activeTab === 'medications'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Pill className="h-3.5 w-3.5" />
                <span>Medications</span>
              </button>
              <button
                onClick={() => setActiveTab('appointments')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md transition ${
                  activeTab === 'appointments'
                    ? 'bg-blue-600 text-white shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Calendar className="h-3.5 w-3.5" />
                <span>Appointments</span>
              </button>
            </div>

            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Feedback alert */}
        {feedback && (
          <div
            className={`px-6 py-2.5 text-xs font-medium flex items-center gap-2 border-b transition ${
              feedback.type === 'success'
                ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                : 'bg-rose-950/80 text-rose-300 border-rose-800'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            )}
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: MEDICATIONS */}
          {activeTab === 'medications' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/60">
                <div className="flex items-center space-x-3">
                  <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={activeOnlyFilter}
                      onChange={(e) => setActiveOnlyFilter(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500 h-3.5 w-3.5"
                    />
                    <span>Active Regimens Only</span>
                  </label>
                  <span className="text-xs text-slate-500">| Total: {medications.length}</span>
                </div>

                <button
                  onClick={() => setShowAddMedModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium shadow-md shadow-blue-500/20 transition cursor-pointer self-start sm:self-auto"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Add Medication</span>
                </button>
              </div>

              {loadingMeds ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-400 mb-2" />
                  <p className="text-xs">Loading medications...</p>
                </div>
              ) : medications.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
                  <Pill className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-300">No medication regimens recorded</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    Keep your prescription courses organized with dosages, frequencies, and active schedule reminders.
                  </p>
                  <button
                    onClick={() => setShowAddMedModal(true)}
                    className="mt-4 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition cursor-pointer"
                  >
                    Add your first medication
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {medications.map((med) => (
                    <div
                      key={med.medication_id}
                      className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition flex flex-col justify-between"
                    >
                      <div>
                        <div className="flex items-start justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-semibold text-white text-sm">{med.medicine_name}</span>
                            <span
                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                                med.is_active
                                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                                  : 'bg-slate-800 text-slate-400 border border-slate-700'
                              }`}
                            >
                              {med.is_active ? 'Active' : 'Completed'}
                            </span>
                          </div>
                          <button
                            onClick={() => handleDeleteMedication(med.medication_id, med.medicine_name)}
                            className="text-slate-500 hover:text-rose-400 transition p-1 cursor-pointer"
                            title="Delete medication"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>

                        <div className="mt-2.5 grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/60">
                            <span className="text-slate-400 block text-[10px] uppercase font-mono">Dosage</span>
                            <span className="text-slate-200 font-medium">{med.dosage}</span>
                          </div>
                          <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800/60">
                            <span className="text-slate-400 block text-[10px] uppercase font-mono">Frequency</span>
                            <span className="text-slate-200 font-medium">{med.frequency}</span>
                          </div>
                        </div>

                        <div className="mt-2.5 flex items-center space-x-2 text-[11px] text-slate-400">
                          <Clock className="h-3 w-3 text-blue-400" />
                          <span>
                            Started: {med.start_date} {med.end_date ? `• Until: ${med.end_date}` : '• Ongoing'}
                          </span>
                        </div>

                        {med.notes && (
                          <div className="mt-2 text-xs text-slate-400 bg-slate-900/50 p-2 rounded border border-slate-800/40">
                            <span className="text-slate-500 font-medium text-[10px] block">Instructions:</span>
                            {med.notes}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: APPOINTMENTS */}
          {activeTab === 'appointments' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-800/60">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-300">
                    <Filter className="h-3.5 w-3.5 text-slate-400" />
                    <span>Status:</span>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                    >
                      <option value="">All Appointments</option>
                      <option value="Upcoming">Upcoming</option>
                      <option value="Completed">Completed</option>
                      <option value="Cancelled">Cancelled</option>
                    </select>
                  </div>
                  <span className="text-xs text-slate-500">| Total: {appointments.length}</span>
                </div>

                <button
                  onClick={() => setShowAddApptModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium shadow-md shadow-blue-500/20 transition cursor-pointer self-start sm:self-auto"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Book Appointment</span>
                </button>
              </div>

              {loadingAppts ? (
                <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-400 mb-2" />
                  <p className="text-xs">Loading appointments...</p>
                </div>
              ) : appointments.length === 0 ? (
                <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
                  <Calendar className="h-10 w-10 text-slate-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-300">No appointments scheduled</p>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    Track clinical follow-ups, doctor consults, and telehealth consultations with date, time, and clinic notes.
                  </p>
                  <button
                    onClick={() => setShowAddApptModal(true)}
                    className="mt-4 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition cursor-pointer"
                  >
                    Schedule an appointment
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {appointments.map((appt) => (
                    <div
                      key={appt.appointment_id}
                      className="p-4 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-slate-700 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      <div className="space-y-1.5">
                        <div className="flex items-center space-x-3">
                          <span className="font-semibold text-white text-sm flex items-center gap-1.5">
                            <User className="h-3.5 w-3.5 text-blue-400" />
                            {appt.doctor_name}
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded bg-blue-950/80 border border-blue-800/60 text-blue-300 font-medium flex items-center gap-1">
                            <Stethoscope className="h-3 w-3" />
                            {appt.specialization}
                          </span>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                              appt.status === 'Upcoming'
                                ? 'bg-amber-950 text-amber-400 border border-amber-800/60'
                                : appt.status === 'Completed'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
                                : 'bg-rose-950 text-rose-400 border border-rose-800/60'
                            }`}
                          >
                            {appt.status}
                          </span>
                        </div>

                        <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-400">
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3.5 w-3.5 text-slate-500" />
                            <span>{appt.appointment_date}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-3.5 w-3.5 text-slate-500" />
                            <span>{appt.appointment_time}</span>
                          </div>
                          {appt.location && (
                            <div className="flex items-center space-x-1 text-slate-300">
                              <MapPin className="h-3.5 w-3.5 text-slate-500" />
                              <span>{appt.location}</span>
                            </div>
                          )}
                        </div>

                        {appt.notes && (
                          <p className="text-xs text-slate-400 bg-slate-900/50 p-2 rounded border border-slate-800/40">
                            {appt.notes}
                          </p>
                        )}
                      </div>

                      <div className="flex items-center space-x-2 shrink-0 self-end md:self-center">
                        {appt.status === 'Upcoming' && (
                          <button
                            onClick={() => handleUpdateApptStatus(appt.appointment_id, 'Completed')}
                            className="px-2.5 py-1 rounded bg-emerald-950 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 text-xs font-medium transition cursor-pointer flex items-center gap-1"
                          >
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Done</span>
                          </button>
                        )}
                        {appt.status === 'Upcoming' && (
                          <button
                            onClick={() => handleUpdateApptStatus(appt.appointment_id, 'Cancelled')}
                            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
                          >
                            Cancel
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteAppointment(appt.appointment_id)}
                          className="text-slate-500 hover:text-rose-400 transition p-1.5 rounded hover:bg-slate-800 cursor-pointer"
                          title="Delete appointment"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* SUB-MODAL: Add Medication */}
        {showAddMedModal && (
          <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl text-slate-100 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                  <Pill className="h-4 w-4 text-blue-400" />
                  Add Prescribed Medication
                </h3>
                <button
                  onClick={() => setShowAddMedModal(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleAddMedication} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Medicine Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Metformin, Atorvastatin, Amoxicillin"
                    value={medForm.medicine_name}
                    onChange={(e) => setMedForm({ ...medForm, medicine_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1">Dosage *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 500mg, 10ml, 1 tab"
                      value={medForm.dosage}
                      onChange={(e) => setMedForm({ ...medForm, dosage: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Frequency *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Twice daily with meals"
                      value={medForm.frequency}
                      onChange={(e) => setMedForm({ ...medForm, frequency: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1">Start Date *</label>
                    <input
                      type="date"
                      required
                      value={medForm.start_date}
                      onChange={(e) => setMedForm({ ...medForm, start_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">End Date (Optional)</label>
                    <input
                      type="date"
                      value={medForm.end_date || ''}
                      onChange={(e) => setMedForm({ ...medForm, end_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Instructions / Notes</label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Take 30 minutes after dinner with plenty of water."
                    value={medForm.notes || ''}
                    onChange={(e) => setMedForm({ ...medForm, notes: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500 resize-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddMedModal(false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingMed}
                    className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition flex items-center gap-1.5"
                  >
                    {submittingMed && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    <span>Save Prescription</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* SUB-MODAL: Add Appointment */}
        {showAddApptModal && (
          <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md shadow-2xl text-slate-100 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-400" />
                  Schedule Doctor Appointment
                </h3>
                <button
                  onClick={() => setShowAddApptModal(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <form onSubmit={handleAddAppointment} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 mb-1">Doctor Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Sarah Jenkins"
                    value={apptForm.doctor_name}
                    onChange={(e) => setApptForm({ ...apptForm, doctor_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Specialization *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Cardiologist, Endocrinologist, General Physician"
                    value={apptForm.specialization}
                    onChange={(e) => setApptForm({ ...apptForm, specialization: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 mb-1">Date *</label>
                    <input
                      type="date"
                      required
                      value={apptForm.appointment_date}
                      onChange={(e) => setApptForm({ ...apptForm, appointment_date: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1">Time *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. 10:30 AM, 14:00"
                      value={apptForm.appointment_time}
                      onChange={(e) => setApptForm({ ...apptForm, appointment_time: e.target.value })}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Location / Clinic</label>
                  <input
                    type="text"
                    placeholder="e.g. Apollo Hospital Suite 302 / Telehealth link"
                    value={apptForm.location || ''}
                    onChange={(e) => setApptForm({ ...apptForm, location: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 mb-1">Reason / Notes</label>
                  <textarea
                    rows={2}
                    placeholder="e.g. Blood pressure evaluation and follow-up lab review."
                    value={apptForm.notes || ''}
                    onChange={(e) => setApptForm({ ...apptForm, notes: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500 resize-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddApptModal(false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingAppt}
                    className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition flex items-center gap-1.5"
                  >
                    {submittingAppt && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                    <span>Confirm Booking</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}
