import React, { useState, useEffect } from 'react'
import {
  X,
  Stethoscope,
  Send,
  Loader2,
  Copy,
  Check,
  PhoneCall,
  ShieldAlert,
  History,
  HeartPulse,
  Info
} from 'lucide-react'
import {
  symptomsService,
  type SymptomAnalysisResponse,
  type SymptomHistoryItem,
  type CommonSymptomCategory
} from '../../services/symptoms'

interface SymptomAssistantModalProps {
  isOpen: boolean
  onClose: () => void
}

export const SymptomAssistantModal: React.FC<SymptomAssistantModalProps> = ({
  isOpen,
  onClose
}) => {
  const [symptoms, setSymptoms] = useState<string>('')
  const [duration, setDuration] = useState<string>('')
  const [severity, setSeverity] = useState<number>(4)
  const [analyzing, setAnalyzing] = useState<boolean>(false)
  const [result, setResult] = useState<SymptomAnalysisResponse | null>(null)
  const [history, setHistory] = useState<SymptomHistoryItem[]>([])
  const [commonCategories, setCommonCategories] = useState<CommonSymptomCategory[]>([])
  const [activeTab, setActiveTab] = useState<'assess' | 'history'>('assess')
  const [copiedQuestions, setCopiedQuestions] = useState<boolean>(false)

  const loadData = async () => {
    try {
      const cats = await symptomsService.getCommonSymptoms()
      setCommonCategories(cats)
    } catch {
      // Handled silently
    }

    try {
      const hist = await symptomsService.getHistory()
      setHistory(hist)
    } catch {
      // Handled silently
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadData()
    }
  }, [isOpen])

  if (!isOpen) return null

  const handleAddSymptomTag = (symptomName: string) => {
    setSymptoms((prev) => {
      if (!prev.trim()) return symptomName
      if (prev.toLowerCase().includes(symptomName.toLowerCase())) return prev
      return `${prev}, ${symptomName}`
    })
  }

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!symptoms.trim() || analyzing) return

    setAnalyzing(true)
    try {
      const res = await symptomsService.analyzeSymptoms({
        symptoms: symptoms.trim(),
        duration: duration.trim() || undefined,
        severity
      })
      setResult(res)
      const hist = await symptomsService.getHistory()
      setHistory(hist)
    } catch {
      alert('Unable to analyze symptoms. Please check network connection.')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleCopyQuestions = () => {
    if (!result?.doctor_questions.length) return
    const text = result.doctor_questions.map((q, idx) => `${idx + 1}. ${q}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopiedQuestions(true)
    setTimeout(() => setCopiedQuestions(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20 shrink-0">
              <Stethoscope className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Symptom Assistant & Clinical Triage</h2>
                <span className="text-[10px] font-mono uppercase bg-amber-950 text-amber-400 border border-amber-800/60 px-2 py-0.5 rounded-full">
                  Phase 7 Triage Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Educational symptom risk evaluation, emergency red-flag screening, and specialist referrals.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* View Switcher Sub-header */}
        <div className="flex items-center justify-between border-b border-slate-800/80 my-3 pb-2 text-xs">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('assess')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'assess'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <HeartPulse className="h-3.5 w-3.5" />
              Symptom Assessment
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'history'
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <History className="h-3.5 w-3.5" />
              Triage History ({history.length})
            </button>
          </div>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {activeTab === 'history' ? (
            /* HISTORY TAB */
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Previous Symptom Evaluations ({history.length})
              </h3>
              {history.length === 0 ? (
                <div className="text-center py-12 text-slate-500 border border-dashed border-slate-800 rounded-xl">
                  <Stethoscope className="mx-auto h-8 w-8 mb-2 text-slate-600" />
                  <p className="text-sm font-medium text-slate-400">No previous symptom evaluations logged.</p>
                  <p className="text-xs text-slate-500 mt-1">Submit an assessment on the main tab to track your history.</p>
                </div>
              ) : (
                history.map((item, idx) => (
                  <div key={idx} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white truncate max-w-md">{item.symptoms}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border ${
                          item.triage_level === 'EMERGENCY'
                            ? 'bg-rose-950 text-rose-300 border-rose-800'
                            : item.triage_level === 'URGENT'
                            ? 'bg-amber-950 text-amber-300 border-amber-800'
                            : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        }`}
                      >
                        {item.triage_level}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-400">
                      <span>Specialist: <strong className="text-slate-200">{item.recommended_specialist}</strong></span>
                      <span className="font-mono text-[10px]">{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className="text-xs text-slate-300 leading-relaxed pt-1 border-t border-slate-800/60">
                      {item.summary_text}
                    </p>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* ASSESSMENT TAB */
            <div className="space-y-4">
              {/* Common Symptom Quick Tags */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3.5 space-y-2">
                <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider block">
                  Quick Select Common Symptoms:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {commonCategories.flatMap((cat) => cat.symptoms).slice(0, 12).map((symptomName, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleAddSymptomTag(symptomName)}
                      className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-amber-700/60 transition"
                    >
                      + {symptomName}
                    </button>
                  ))}
                </div>
              </div>

              {/* Assessment Form */}
              <form onSubmit={handleAnalyze} className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Describe your symptoms, how they feel, and when they started:
                  </label>
                  <textarea
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    rows={3}
                    placeholder="e.g., Dull aching chest tightness for 2 hours, mild shortness of breath on climbing stairs, lightheadedness..."
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Duration / Timeline:
                    </label>
                    <input
                      type="text"
                      value={duration}
                      onChange={(e) => setDuration(e.target.value)}
                      placeholder="e.g., 2 hours, 3 days, 1 week"
                      className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500"
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-medium text-slate-300">
                        Self-Reported Severity: <span className="text-amber-400 font-bold">{severity} / 10</span>
                      </label>
                      <span className="text-[10px] text-slate-500">
                        {severity <= 3 ? 'Mild' : severity <= 7 ? 'Moderate' : 'Severe'}
                      </span>
                    </div>
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={severity}
                      onChange={(e) => setSeverity(Number(e.target.value))}
                      className="w-full accent-amber-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={!symptoms.trim() || analyzing}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 via-rose-500 to-rose-600 text-white text-xs font-bold hover:from-amber-400 hover:to-rose-500 transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-lg shadow-rose-950/20"
                >
                  {analyzing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  {analyzing ? 'Evaluating Clinical Risk & Red Flags...' : 'Analyze Symptoms & Triage Urgency'}
                </button>
              </form>

              {/* Assessment Results View */}
              {result && (
                <div className="space-y-4 pt-2">
                  {/* RED-FLAG EMERGENCY BANNER (If Triggered) */}
                  {result.is_emergency && (
                    <div className="rounded-2xl border-2 border-rose-600 bg-rose-950/40 p-4 space-y-3 animate-pulse">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-rose-600 flex items-center justify-center text-white shrink-0">
                          <PhoneCall className="h-5 w-5" />
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-rose-200 uppercase tracking-wide">
                            Emergency Red-Flag Detected
                          </h4>
                          <p className="text-xs text-rose-300">
                            Immediate emergency medical care is strongly advised. Call emergency services (911/112).
                          </p>
                        </div>
                      </div>

                      <div className="space-y-1.5 pt-1 border-t border-rose-800/60">
                        {result.red_flags.map((rf, idx) => (
                          <div key={idx} className="text-xs text-rose-200 bg-rose-950/60 p-2.5 rounded-lg border border-rose-800">
                            <strong>{rf.symptom}:</strong> {rf.urgency_reason}
                            <div className="text-[11px] text-rose-300 font-semibold mt-1">
                              Action Required: {rf.action_required}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Triage Overview Card */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider border ${
                            result.triage_level === 'EMERGENCY'
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : result.triage_level === 'URGENT'
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}
                        >
                          Triage: {result.triage_level}
                        </span>

                        <span className="text-xs text-slate-300 flex items-center gap-1">
                          <Stethoscope className="h-3.5 w-3.5 text-amber-400" />
                          Specialist: <strong className="text-white">{result.recommended_specialist}</strong>
                        </span>
                      </div>

                      <button
                        onClick={handleCopyQuestions}
                        className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition"
                      >
                        {copiedQuestions ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-400" /> Questions Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" /> Copy Doctor Questions
                          </>
                        )}
                      </button>
                    </div>

                    <div>
                      <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-1">
                        Clinical Overview
                      </h4>
                      <p className="text-xs text-slate-200 leading-relaxed">{result.clinical_assessment}</p>
                    </div>

                    {/* Educational Considerations */}
                    {result.possible_causes.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                          Potential Considerations (Non-Diagnostic)
                        </h4>
                        <ul className="space-y-1">
                          {result.possible_causes.map((cause, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                              <span>{cause}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Supportive Comfort Tips */}
                    {result.supportive_care_tips.length > 0 && (
                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                        <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                          <HeartPulse className="h-3.5 w-3.5" /> Supportive Care Considerations
                        </h4>
                        <ul className="space-y-1">
                          {result.supportive_care_tips.map((tip, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                              <span>{tip}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Questions for Physician */}
                    {result.doctor_questions.length > 0 && (
                      <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                        <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                          <ShieldAlert className="h-3.5 w-3.5" /> Discussion Points for Your Doctor
                        </h4>
                        <ul className="space-y-1.5">
                          {result.doctor_questions.map((q, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-xs text-slate-200">
                              <span className="h-4 w-4 rounded-md bg-indigo-950 border border-indigo-800 flex items-center justify-center text-[10px] text-indigo-300 shrink-0 font-bold">
                                {idx + 1}
                              </span>
                              <span>{q}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* Safety Disclaimer Banner */}
                  <div className="rounded-xl border border-amber-900/30 bg-amber-950/20 p-3 flex items-start gap-2.5 text-[11px] text-amber-300/90">
                    <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <p className="leading-normal">{result.disclaimer}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
