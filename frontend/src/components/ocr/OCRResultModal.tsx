import React, { useState, useEffect } from 'react'
import {
  X,
  Brain,
  FileText,
  Layers,
  Copy,
  Check,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  Table
} from 'lucide-react'
import { ocrService, type OCRData, type ReportChunkItem } from '../../services/ocr'

interface OCRResultModalProps {
  isOpen: boolean
  onClose: () => void
  reportId: string
  reportFileName: string
  onStatusUpdated?: () => void
}

export const OCRResultModal: React.FC<OCRResultModalProps> = ({
  isOpen,
  onClose,
  reportId,
  reportFileName,
  onStatusUpdated
}) => {
  const [activeTab, setActiveTab] = useState<'parameters' | 'text' | 'chunks'>('parameters')
  const [data, setData] = useState<OCRData | null>(null)
  const [chunks, setChunks] = useState<ReportChunkItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [reprocessing, setReprocessing] = useState<boolean>(false)
  const [copied, setCopied] = useState<boolean>(false)

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await ocrService.getOCRData(reportId)
      setData(res)
      if (onStatusUpdated) onStatusUpdated()
      // Also fetch chunks
      try {
        const chunkRes = await ocrService.getChunks(reportId)
        setChunks(chunkRes.chunks)
      } catch {
        // Chunks might be empty or fallback
      }
    } catch {
      // Error handling
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && reportId) {
      loadData()
    }
  }, [isOpen, reportId])

  if (!isOpen) return null

  const handleReprocess = async () => {
    setReprocessing(true)
    try {
      const res = await ocrService.processOCR(reportId)
      setData(res)
      const chunkRes = await ocrService.getChunks(reportId)
      setChunks(chunkRes.chunks)
      if (onStatusUpdated) onStatusUpdated()
    } catch {
      alert('Failed to re-process document OCR.')
    } finally {
      setReprocessing(false)
    }
  }

  const handleCopyText = () => {
    if (data?.extracted_text) {
      navigator.clipboard.writeText(data.extracted_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20 shrink-0">
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white truncate max-w-sm sm:max-w-md">
                  {reportFileName}
                </h2>
                {data && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 border border-emerald-800 text-emerald-400">
                    {(data.confidence * 100).toFixed(0)}% Confidence
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                OCR Clinical Text &amp; Structured Finding Extraction
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleReprocess}
              disabled={reprocessing || loading}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-400 hover:text-white transition disabled:opacity-50"
              title="Re-run OCR Processing"
            >
              <RefreshCw className={`h-4 w-4 ${reprocessing ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="my-4 flex rounded-lg bg-slate-950 p-1 border border-slate-800">
          <button
            onClick={() => setActiveTab('parameters')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 transition ${
              activeTab === 'parameters'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Table className="h-3.5 w-3.5" />
            <span>Lab Findings ({data?.parameters.length ?? 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('text')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 transition ${
              activeTab === 'text'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Extracted Text</span>
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md flex items-center justify-center gap-1.5 transition ${
              activeTab === 'chunks'
                ? 'bg-cyan-600 text-white shadow'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>RAG Chunks ({data?.total_chunks ?? chunks.length})</span>
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto pr-1">
          {loading ? (
            <div className="py-20 text-center text-xs text-slate-400 flex flex-col items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-400 mb-3" />
              <span>Analyzing document and extracting clinical text...</span>
            </div>
          ) : !data ? (
            <div className="py-16 text-center text-xs text-slate-500">
              No OCR data could be extracted from this document.
            </div>
          ) : activeTab === 'parameters' ? (
            <div>
              {data.parameters.length === 0 ? (
                <div className="py-12 text-center text-xs text-slate-400 border border-dashed border-slate-800 rounded-xl">
                  <p className="font-medium text-slate-300">No tabular laboratory parameters detected.</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Check the "Extracted Text" tab to review the complete unformatted text.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                        <th className="py-2.5 px-3">Test Parameter</th>
                        <th className="py-2.5 px-3">Observed Value</th>
                        <th className="py-2.5 px-3">Reference Interval</th>
                        <th className="py-2.5 px-3 text-right">Clinical Flag</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/30">
                      {data.parameters.map((param, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/20 transition">
                          <td className="py-2.5 px-3 font-medium text-white">{param.name}</td>
                          <td className="py-2.5 px-3 text-cyan-300 font-mono font-semibold">
                            {param.value} {param.unit && <span className="text-slate-400 text-[11px] font-normal">{param.unit}</span>}
                          </td>
                          <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                            {param.reference_range || '-'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              param.status === 'HIGH'
                                ? 'bg-rose-950/80 text-rose-400 border-rose-800'
                                : param.status === 'LOW'
                                ? 'bg-amber-950/80 text-amber-400 border-amber-800'
                                : param.status === 'NORMAL'
                                ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                                : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}>
                              {param.status === 'NORMAL' && <CheckCircle2 className="h-2.5 w-2.5" />}
                              {(param.status === 'HIGH' || param.status === 'LOW') && <AlertTriangle className="h-2.5 w-2.5" />}
                              {param.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : activeTab === 'text' ? (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-400">
                <span>{data.extracted_text.length} characters extracted</span>
                <button
                  onClick={handleCopyText}
                  className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 transition"
                >
                  {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy Text'}</span>
                </button>
              </div>
              <pre className="p-4 rounded-xl border border-slate-800 bg-slate-950/80 text-xs font-mono text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[50vh] overflow-y-auto">
                {data.extracted_text || 'No text extracted.'}
              </pre>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-xs text-slate-400">
                These semantic chunks will be embedded for grounded RAG Q&amp;A retrieval in Phase 6.
              </p>
              <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
                {chunks.map((chunk, idx) => (
                  <div
                    key={chunk.chunk_id || idx}
                    className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/80 pb-1">
                      <span className="font-semibold text-cyan-400">Chunk #{idx + 1}</span>
                      <span>Page {chunk.page_number || '1'} &bull; {chunk.chunk_text.length} chars</span>
                    </div>
                    <p className="text-xs text-slate-300 font-mono leading-relaxed">
                      {chunk.chunk_text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="pt-4 mt-4 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 text-white hover:bg-slate-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
