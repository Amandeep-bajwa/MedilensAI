import React, { useState, useEffect } from 'react'
import {
  X,
  Sparkles,
  AlertTriangle,
  HeartPulse,
  MessageSquare,
  Send,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  ShieldCheck,
  Stethoscope,
  Info
} from 'lucide-react'
import {
  aiService,
  type ReportExplanationResponse,
  type AbnormalFindingItem
} from '../../services/ai'

interface AIExplanationModalProps {
  isOpen: boolean
  onClose: () => void
  reportId: string
  reportFileName: string
}

export const AIExplanationModal: React.FC<AIExplanationModalProps> = ({
  isOpen,
  onClose,
  reportId,
  reportFileName
}) => {
  const [activeTab, setActiveTab] = useState<'summary' | 'abnormal' | 'doctor' | 'chat'>('summary')
  const [explanation, setExplanation] = useState<ReportExplanationResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [generating, setGenerating] = useState<boolean>(false)
  const [focusArea, setFocusArea] = useState<string>('')
  const [copiedDoctorQuestions, setCopiedDoctorQuestions] = useState<boolean>(false)

  // Interactive Q&A state
  const [userQuestion, setUserQuestion] = useState<string>('')
  const [isAsking, setIsAsking] = useState<boolean>(false)
  const [chatMessages, setChatMessages] = useState<
    Array<{ sender: 'user' | 'ai'; text: string; disclaimer?: string; time: string }>
  >([])

  const loadExplanation = async () => {
    setLoading(true)
    try {
      // First try to fetch existing or generate on-demand
      const data = await aiService.getExplanation(reportId)
      setExplanation(data)
    } catch {
      // If none yet or error, trigger explainReport
      try {
        const generated = await aiService.explainReport(reportId)
        setExplanation(generated)
      } catch {
        // Fallback error state
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && reportId) {
      loadExplanation()
      setChatMessages([])
      setUserQuestion('')
    }
  }, [isOpen, reportId])

  if (!isOpen) return null

  const handleRegenerate = async () => {
    setGenerating(true)
    try {
      const data = await aiService.explainReport(reportId, focusArea.trim() || undefined)
      setExplanation(data)
    } catch {
      alert('Failed to synthesize AI clinical explanation. Please verify document status.')
    } finally {
      setGenerating(false)
    }
  }

  const handleCopyDoctorQuestions = () => {
    if (!explanation?.doctor_questions.length) return
    const text = explanation.doctor_questions.map((q, idx) => `${idx + 1}. ${q}`).join('\n')
    navigator.clipboard.writeText(text)
    setCopiedDoctorQuestions(true)
    setTimeout(() => setCopiedDoctorQuestions(false), 2000)
  }

  const handleSendQuestion = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userQuestion.trim() || isAsking) return

    const q = userQuestion.trim()
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

    setChatMessages((prev) => [...prev, { sender: 'user', text: q, time: now }])
    setUserQuestion('')
    setIsAsking(true)

    try {
      const res = await aiService.askQuestion(reportId, q)
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: res.answer,
          disclaimer: res.disclaimer,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ])
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: 'Unable to analyze question against this clinical report. Please ensure the document contains parsed findings.',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ])
    } finally {
      setIsAsking(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20 shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">AI Clinical Explanation</h2>
                {explanation?.provider_used && (
                  <span className="text-[10px] font-mono uppercase bg-cyan-950 text-cyan-400 border border-cyan-800/60 px-2 py-0.5 rounded-full">
                    {explanation.provider_used}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 truncate max-w-md">
                Document: <span className="text-slate-200 font-medium">{reportFileName}</span>
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

        {/* Tab Controls */}
        <div className="flex items-center justify-between border-b border-slate-800/80 my-3 pb-2 text-xs">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('summary')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'summary'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <HeartPulse className="h-3.5 w-3.5" />
              Executive Summary
            </button>
            <button
              onClick={() => setActiveTab('abnormal')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'abnormal'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Abnormal Flags
              {explanation?.abnormal_findings && explanation.abnormal_findings.length > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded-full bg-amber-500/30 text-amber-300 text-[10px] font-bold">
                  {explanation.abnormal_findings.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab('doctor')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'doctor'
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Stethoscope className="h-3.5 w-3.5" />
              Doctor Questions
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
                activeTab === 'chat'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Ask AI Follow-Up
            </button>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={focusArea}
              onChange={(e) => setFocusArea(e.target.value)}
              className="rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">General Analysis</option>
              <option value="metabolic health">Metabolic Health</option>
              <option value="cardiovascular risk">Cardiovascular Risk</option>
              <option value="renal function">Renal Function</option>
              <option value="hematology">Hematology</option>
            </select>
            <button
              onClick={handleRegenerate}
              disabled={generating}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800/80 text-slate-300 hover:text-white hover:border-slate-600 transition disabled:opacity-50 text-[11px]"
              title="Re-run AI Synthesis"
            >
              <RefreshCw className={`h-3 w-3 ${generating ? 'animate-spin text-cyan-400' : ''}`} />
              {generating ? 'Regenerating...' : 'Re-analyze'}
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {loading ? (
            <div className="py-20 text-center text-slate-400">
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-cyan-400 mb-2" />
              <p className="text-sm font-medium">Synthesizing clinical insights and jargon-free explanations...</p>
            </div>
          ) : !explanation ? (
            <div className="py-16 text-center text-slate-400 border border-dashed border-slate-800 rounded-xl">
              <AlertTriangle className="mx-auto h-8 w-8 text-amber-400 mb-2" />
              <p className="text-sm font-medium text-slate-200">No explanation available</p>
              <p className="text-xs text-slate-500 mt-1">
                Click re-analyze above or ensure the document has completed OCR extraction.
              </p>
            </div>
          ) : (
            <>
              {/* TAB 1: EXECUTIVE SUMMARY */}
              {activeTab === 'summary' && (
                <div className="space-y-4">
                  {/* Synthesis Paragraph */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                    <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" /> High-Level Summary
                    </h3>
                    <p className="text-sm text-slate-200 leading-relaxed font-sans">
                      {explanation.summary}
                    </p>
                  </div>

                  {/* Key Findings */}
                  {explanation.key_findings.length > 0 && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
                        Key Clinical Highlights
                      </h3>
                      <ul className="space-y-2">
                        {explanation.key_findings.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Lifestyle Recommendations */}
                  {explanation.lifestyle_recommendations.length > 0 && (
                    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                      <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                        <HeartPulse className="h-3.5 w-3.5" /> General Wellness Considerations
                      </h3>
                      <ul className="space-y-2">
                        {explanation.lifestyle_recommendations.map((tip, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-xs text-slate-300">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                            <span>{tip}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: ABNORMAL FINDINGS */}
              {activeTab === 'abnormal' && (
                <div className="space-y-3">
                  {explanation.abnormal_findings.length === 0 ? (
                    <div className="rounded-xl border border-emerald-900/40 bg-emerald-950/20 p-6 text-center text-emerald-300">
                      <ShieldCheck className="mx-auto h-8 w-8 text-emerald-400 mb-2" />
                      <p className="text-sm font-semibold">No Out-Of-Range Biomarkers Detected</p>
                      <p className="text-xs text-emerald-400/80 mt-1">
                        All parsed clinical parameters fall within expected physiological reference intervals.
                      </p>
                    </div>
                  ) : (
                    explanation.abnormal_findings.map((finding: AbnormalFindingItem, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-amber-900/40 bg-amber-950/10 p-4 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-white">{finding.parameter_name}</span>
                            <span
                              className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                                finding.flag === 'HIGH'
                                  ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                  : 'bg-amber-950 text-amber-300 border border-amber-800'
                              }`}
                            >
                              {finding.flag}
                            </span>
                          </div>
                          <div className="text-right text-xs">
                            <span className="text-slate-400">Observed: </span>
                            <span className="font-semibold text-white">{finding.observed_value}</span>
                            <span className="text-slate-500 text-[11px] ml-2 font-mono">
                              (Ref: {finding.reference_interval})
                            </span>
                          </div>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed border-t border-slate-800/60 pt-2">
                          <span className="font-medium text-amber-300">Clinical Context: </span>
                          {finding.plain_english_explanation}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* TAB 3: DOCTOR QUESTIONS */}
              {activeTab === 'doctor' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs text-slate-400">
                      Prepared discussion points to bring to your next healthcare appointment:
                    </p>
                    <button
                      onClick={handleCopyDoctorQuestions}
                      className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition"
                    >
                      {copiedDoctorQuestions ? (
                        <>
                          <Check className="h-3 w-3 text-emerald-400" /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" /> Copy All Questions
                        </>
                      )}
                    </button>
                  </div>

                  <div className="space-y-2">
                    {explanation.doctor_questions.map((question, idx) => (
                      <div
                        key={idx}
                        className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex items-start gap-3"
                      >
                        <div className="h-6 w-6 rounded-lg bg-indigo-950/80 border border-indigo-800/40 text-indigo-400 text-xs font-bold flex items-center justify-center shrink-0">
                          {idx + 1}
                        </div>
                        <p className="text-xs text-slate-200 leading-relaxed pt-0.5">{question}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 4: ASK AI FOLLOW-UP */}
              {activeTab === 'chat' && (
                <div className="flex flex-col h-[380px]">
                  <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-3">
                    <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 flex items-start gap-2">
                      <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                      <span>
                        Ask any follow-up questions about this specific report (e.g., "What does high LDL
                        mean for cardiovascular risk?" or "Are there dietary factors affecting creatinine?").
                      </span>
                    </div>

                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex flex-col ${
                          msg.sender === 'user' ? 'items-end' : 'items-start'
                        }`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs ${
                            msg.sender === 'user'
                              ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-none'
                              : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-none'
                          }`}
                        >
                          <p className="leading-relaxed">{msg.text}</p>
                          {msg.disclaimer && (
                            <p className="text-[10px] text-amber-300/80 mt-2 border-t border-slate-700/60 pt-1.5 italic">
                              {msg.disclaimer}
                            </p>
                          )}
                        </div>
                        <span className="text-[9px] text-slate-500 mt-1 px-1 font-mono">
                          {msg.time}
                        </span>
                      </div>
                    ))}

                    {isAsking && (
                      <div className="flex items-center gap-2 text-xs text-slate-400 italic">
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-cyan-400" />
                        Analyzing report context...
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleSendQuestion} className="flex gap-2">
                    <input
                      type="text"
                      value={userQuestion}
                      onChange={(e) => setUserQuestion(e.target.value)}
                      placeholder="Ask a question about this report's findings..."
                      disabled={isAsking}
                      className="flex-1 rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 disabled:opacity-50"
                    />
                    <button
                      type="submit"
                      disabled={!userQuestion.trim() || isAsking}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-xs font-semibold hover:from-cyan-400 hover:to-blue-500 transition disabled:opacity-50 flex items-center gap-1.5"
                    >
                      <Send className="h-3.5 w-3.5" />
                      Send
                    </button>
                  </form>
                </div>
              )}

              {/* Safety Disclaimer Banner */}
              <div className="rounded-xl border border-amber-900/30 bg-amber-950/20 p-3 flex items-start gap-2.5 text-[11px] text-amber-300/90 mt-3">
                <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <p className="leading-normal">{explanation.disclaimer}</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
