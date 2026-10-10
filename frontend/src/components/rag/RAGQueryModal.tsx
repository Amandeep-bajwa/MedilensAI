import React, { useState, useEffect } from 'react'
import {
  X,
  Search,
  BookOpen,
  Send,
  Loader2,
  RefreshCw,
  Copy,
  Check,
  AlertTriangle,
  CheckCircle2,
  Layers,
  History,
  Sparkles,
  Info
} from 'lucide-react'
import {
  ragService,
  type RAGQueryResponse,
  type RAGIndexStatusResponse,
  type RAGHistoryItem
} from '../../services/rag'

interface RAGQueryModalProps {
  isOpen: boolean
  onClose: () => void
  reportId: string
  reportFileName: string
}

export const RAGQueryModal: React.FC<RAGQueryModalProps> = ({
  isOpen,
  onClose,
  reportId,
  reportFileName
}) => {
  const [question, setQuestion] = useState<string>('')
  const [asking, setAsking] = useState<boolean>(false)
  const [lastResponse, setLastResponse] = useState<RAGQueryResponse | null>(null)
  const [indexStatus, setIndexStatus] = useState<RAGIndexStatusResponse | null>(null)
  const [reindexing, setReindexing] = useState<boolean>(false)
  const [history, setHistory] = useState<RAGHistoryItem[]>([])
  const [activeView, setActiveView] = useState<'query' | 'history'>('query')
  const [copiedAnswer, setCopiedAnswer] = useState<boolean>(false)

  const suggestedQuestions = [
    'What are my fasting blood glucose findings?',
    'Explain my cholesterol and lipid panel results',
    'Are my kidney and creatinine levels normal?',
    'What do the clinical notes or physician remarks state?'
  ]

  const loadStatusAndHistory = async () => {
    try {
      const statusRes = await ragService.getIndexStatus(reportId)
      setIndexStatus(statusRes)
    } catch {
      // Handled silently
    }

    try {
      const hist = await ragService.getHistory(reportId)
      setHistory(hist)
    } catch {
      // Handled silently
    }
  }

  useEffect(() => {
    if (isOpen && reportId) {
      setQuestion('')
      setLastResponse(null)
      loadStatusAndHistory()
    }
  }, [isOpen, reportId])

  if (!isOpen) return null

  const handleRunQuery = async (queryText: string) => {
    const q = queryText.trim()
    if (!q || asking) return

    setAsking(true)
    try {
      const res = await ragService.queryRAG(reportId, q)
      setLastResponse(res)
      loadStatusAndHistory()
    } catch {
      alert('Failed to execute grounded query against report chunks.')
    } finally {
      setAsking(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleRunQuery(question)
  }

  const handleReindex = async () => {
    setReindexing(true)
    try {
      await ragService.reindexChunks(reportId)
      await loadStatusAndHistory()
      alert('Semantic document chunks successfully re-indexed.')
    } catch {
      alert('Failed to re-index document chunks.')
    } finally {
      setReindexing(false)
    }
  }

  const handleCopyAnswer = () => {
    if (!lastResponse?.answer) return
    navigator.clipboard.writeText(lastResponse.answer)
    setCopiedAnswer(true)
    setTimeout(() => setCopiedAnswer(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 shrink-0">
              <BookOpen className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white">Report-Grounded RAG Assistant</h2>
                <span className="text-[10px] font-mono uppercase bg-indigo-950 text-indigo-400 border border-indigo-800/60 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Sparkles className="h-2.5 w-2.5" /> Dense Semantic v1
                </span>
              </div>
              <p className="text-xs text-slate-400 truncate max-w-md">
                Grounded strictly in: <span className="text-slate-200 font-medium">{reportFileName}</span>
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

        {/* Index Status Sub-header */}
        <div className="flex flex-wrap items-center justify-between gap-2 py-2.5 px-3 bg-slate-950/60 border-b border-slate-800/80 rounded-lg my-3 text-xs">
          <div className="flex items-center gap-4 text-slate-400">
            <span className="flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-indigo-400" />
              Indexed Chunks: <strong className="text-slate-200">{indexStatus?.total_chunks ?? 0}</strong>
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${indexStatus?.status === 'Indexed' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              Index Status: <strong className="text-slate-200">{indexStatus?.status ?? 'Detecting...'}</strong>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveView(activeView === 'query' ? 'history' : 'query')}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition text-[11px]"
            >
              <History className="h-3 w-3" />
              {activeView === 'query' ? `History (${history.length})` : 'Back to Q&A'}
            </button>
            <button
              onClick={handleReindex}
              disabled={reindexing}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition disabled:opacity-50 text-[11px]"
              title="Re-index document chunks and update semantic representations"
            >
              <RefreshCw className={`h-3 w-3 ${reindexing ? 'animate-spin text-indigo-400' : ''}`} />
              {reindexing ? 'Re-indexing...' : 'Re-index Chunks'}
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-4">
          {activeView === 'history' ? (
            /* History View */
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Previous Grounded Queries ({history.length})
              </h3>
              {history.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No previous inquiries on this document.</p>
              ) : (
                history.map((item, idx) => (
                  <div key={idx} className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 space-y-2">
                    <div className="text-xs font-semibold text-indigo-300 flex items-center justify-between">
                      <span>Q: {item.question}</span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">{item.response}</p>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* Main Query View */
            <div className="space-y-4">
              {/* Question Input Form */}
              <form onSubmit={handleSubmit} className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a question strictly grounded in this clinical report..."
                    disabled={asking}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
                  />
                </div>
                <button
                  type="submit"
                  disabled={!question.trim() || asking}
                  className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold hover:from-indigo-400 hover:to-purple-500 transition disabled:opacity-50 flex items-center gap-1.5 shadow-md shadow-indigo-500/10"
                >
                  {asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Ask RAG
                </button>
              </form>

              {/* Suggested Questions Chips */}
              <div className="flex flex-wrap gap-1.5 items-center">
                <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mr-1">
                  Sample Prompts:
                </span>
                {suggestedQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuestion(q)
                      handleRunQuery(q)
                    }}
                    disabled={asking}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-indigo-800 transition disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Query Response State */}
              {asking && (
                <div className="py-16 text-center text-slate-400">
                  <Loader2 className="mx-auto h-8 w-8 animate-spin text-indigo-400 mb-2" />
                  <p className="text-sm font-medium">Retrieving semantic document chunks and verifying citations...</p>
                </div>
              )}

              {lastResponse && !asking && (
                <div className="space-y-4 pt-2">
                  {/* Grounded Answer Card */}
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 space-y-3">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                            lastResponse.is_grounded
                              ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                              : 'bg-amber-950 text-amber-300 border-amber-800'
                          }`}
                        >
                          {lastResponse.is_grounded ? (
                            <>
                              <CheckCircle2 className="h-3 w-3" /> Grounded in Report
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="h-3 w-3" /> Not Found / Refusal
                            </>
                          )}
                        </span>

                        <span className="text-[11px] text-slate-400">
                          Relevance: <strong className="text-white">{(lastResponse.confidence_score * 100).toFixed(0)}%</strong>
                        </span>
                      </div>

                      <button
                        onClick={handleCopyAnswer}
                        className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md border border-slate-700 bg-slate-800 text-slate-300 hover:text-white transition"
                      >
                        {copiedAnswer ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-400" /> Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" /> Copy
                          </>
                        )}
                      </button>
                    </div>

                    <div className="text-xs text-slate-200 leading-relaxed whitespace-pre-line font-sans">
                      {lastResponse.answer}
                    </div>
                  </div>

                  {/* Grounding Source Citations Drawer */}
                  {lastResponse.citations.length > 0 && (
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Layers className="h-3.5 w-3.5" /> Source Citations ({lastResponse.citations.length})
                      </h4>
                      <div className="grid grid-cols-1 gap-2">
                        {lastResponse.citations.map((citation, idx) => (
                          <div
                            key={idx}
                            className="rounded-xl border border-indigo-900/40 bg-indigo-950/20 p-3 space-y-1.5"
                          >
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-semibold text-indigo-300 flex items-center gap-1.5">
                                <span className="h-4 w-4 rounded-md bg-indigo-900 flex items-center justify-center text-[10px] text-white">
                                  {idx + 1}
                                </span>
                                Page {citation.page_number}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                Match: {(citation.relevance_score * 100).toFixed(0)}% | ID: {citation.chunk_id.slice(0, 8)}...
                              </span>
                            </div>
                            <p className="text-xs text-slate-300 font-mono bg-slate-950/60 p-2 rounded-lg border border-slate-800/60 leading-relaxed">
                              "{citation.snippet}"
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Safety Disclaimer Banner */}
                  <div className="rounded-xl border border-amber-900/30 bg-amber-950/20 p-3 flex items-start gap-2.5 text-[11px] text-amber-300/90">
                    <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                    <p className="leading-normal">{lastResponse.disclaimer}</p>
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
