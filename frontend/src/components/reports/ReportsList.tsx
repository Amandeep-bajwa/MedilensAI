import React, { useState, useEffect } from 'react'
import {
  FileText,
  Download,
  Trash2,
  Search,
  RefreshCw,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Brain,
  Sparkles,
  BookOpen
} from 'lucide-react'
import { reportsService, type ReportItem } from '../../services/reports'
import { OCRResultModal } from '../ocr/OCRResultModal'
import { AIExplanationModal } from '../ai/AIExplanationModal'
import { RAGQueryModal } from '../rag/RAGQueryModal'

interface ReportsListProps {
  refreshTrigger: number
  onReportDeleted?: () => void
}

export const ReportsList: React.FC<ReportsListProps> = ({ refreshTrigger, onReportDeleted }) => {
  const [reports, setReports] = useState<ReportItem[]>([])
  const [total, setTotal] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)
  const [search, setSearch] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  
  // OCR, AI & RAG Modal state
  const [selectedReportForOCR, setSelectedReportForOCR] = useState<ReportItem | null>(null)
  const [selectedReportForAI, setSelectedReportForAI] = useState<ReportItem | null>(null)
  const [selectedReportForRAG, setSelectedReportForRAG] = useState<ReportItem | null>(null)


  const loadReports = async () => {
    setLoading(true)
    try {
      const data = await reportsService.listReports({
        skip: 0,
        limit: 50,
        search: search.trim() || undefined,
        category: categoryFilter || undefined
      })
      setReports(data.items)
      setTotal(data.total)
    } catch {
      // Handled silently
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [refreshTrigger, categoryFilter])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    loadReports()
  }

  const handleDownload = async (report: ReportItem) => {
    try {
      await reportsService.downloadReport(report.report_id, report.file_name)
    } catch {
      alert('Unable to download report. File may not exist on disk.')
    }
  }

  const handleDelete = async (reportId: string) => {
    if (!window.confirm('Are you sure you want to delete this clinical report? This action is permanent.')) {
      return
    }
    setDeletingId(reportId)
    try {
      await reportsService.deleteReport(reportId)
      setReports((prev) => prev.filter((r) => r.report_id !== reportId))
      setTotal((prev) => prev - 1)
      if (onReportDeleted) onReportDeleted()
    } catch {
      alert('Failed to delete report.')
    } finally {
      setDeletingId(null)
    }
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl shadow-cyan-950/5">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Layers className="h-5 w-5 text-cyan-400" /> Patient Clinical Documents
          </h3>
          <p className="text-xs text-slate-400">
            {total} {total === 1 ? 'report' : 'reports'} ingested in secure repository
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <form onSubmit={handleSearchSubmit} className="relative flex-1 sm:w-48">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search reports..."
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 pl-8 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500"
            />
          </form>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Categories</option>
            <option value="CBC">CBC</option>
            <option value="Lipid Profile">Lipid Profile</option>
            <option value="Blood Glucose">Blood Glucose</option>
            <option value="Thyroid Profile">Thyroid Profile</option>
            <option value="Other">Other</option>
          </select>

          <button
            onClick={loadReports}
            className="rounded-lg border border-slate-800 bg-slate-950 p-2 text-slate-400 hover:text-white hover:border-slate-700 transition"
            title="Refresh list"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Reports Table */}
      {loading ? (
        <div className="py-12 text-center text-xs text-slate-500">
          <RefreshCw className="mx-auto h-6 w-6 animate-spin text-cyan-500 mb-2" />
          Loading clinical documents...
        </div>
      ) : reports.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 py-12 text-center text-slate-500">
          <FileText className="mx-auto h-10 w-10 text-slate-600 mb-2" />
          <p className="text-sm font-medium text-slate-300">No medical reports uploaded yet</p>
          <p className="text-xs text-slate-500 mt-1">
            Upload your first lab document using the form above to begin OCR and analysis.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                <th className="pb-3 pl-2">Document</th>
                <th className="pb-3">Category</th>
                <th className="pb-3">Status</th>
                <th className="pb-3">Size</th>
                <th className="pb-3">Uploaded</th>
                <th className="pb-3 text-right pr-2">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {reports.map((report) => (
                <tr key={report.report_id} className="hover:bg-slate-800/30 transition group">
                  <td className="py-3 pl-2 font-medium text-white flex items-center gap-2">
                    <div className="h-7 w-7 rounded-lg bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center text-cyan-400 shrink-0">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <div className="truncate max-w-[200px] sm:max-w-xs">{report.file_name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">ID: {report.report_id.slice(0, 8)}...</div>
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="inline-block px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">
                      {report.category}
                    </span>
                  </td>
                  <td className="py-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      report.processing_status === 'Completed'
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                        : report.processing_status === 'Processing'
                        ? 'bg-amber-950 text-amber-400 border-amber-800'
                        : report.processing_status === 'Failed'
                        ? 'bg-rose-950 text-rose-400 border-rose-800'
                        : 'bg-cyan-950 text-cyan-400 border-cyan-800'
                    }`}>
                      {report.processing_status === 'Completed' && <CheckCircle2 className="h-2.5 w-2.5" />}
                      {report.processing_status === 'Uploaded' && <Clock className="h-2.5 w-2.5" />}
                      {report.processing_status === 'Failed' && <AlertTriangle className="h-2.5 w-2.5" />}
                      {report.processing_status}
                    </span>
                  </td>
                  <td className="py-3 text-slate-400 font-mono text-[11px]">
                    {formatFileSize(report.file_size_bytes)}
                  </td>
                  <td className="py-3 text-slate-400 text-[11px]">
                    {new Date(report.uploaded_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 text-right pr-2 space-x-1">
                    <button
                      onClick={() => setSelectedReportForRAG(report)}
                      className="p-1.5 rounded-lg border border-purple-800/60 bg-purple-950/40 text-purple-400 hover:bg-purple-900/60 transition"
                      title="Report-Grounded RAG Q&A Assistant"
                    >
                      <BookOpen className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setSelectedReportForAI(report)}
                      className="p-1.5 rounded-lg border border-indigo-800/60 bg-indigo-950/40 text-indigo-400 hover:bg-indigo-900/60 transition"
                      title="AI Clinical Summary & Insights"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setSelectedReportForOCR(report)}
                      className="p-1.5 rounded-lg border border-cyan-800/60 bg-cyan-950/40 text-cyan-400 hover:bg-cyan-900/60 transition"
                      title="View OCR Extracted Findings & Text"
                    >
                      <Brain className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDownload(report)}
                      className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-cyan-400 hover:border-cyan-800 transition"
                      title="Download Original Document"
                    >
                      <Download className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDelete(report.report_id)}
                      disabled={deletingId === report.report_id}
                      className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-rose-400 hover:border-rose-800 transition disabled:opacity-50"
                      title="Delete Report"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* OCR Result Modal */}
      {selectedReportForOCR && (
        <OCRResultModal
          isOpen={!!selectedReportForOCR}
          onClose={() => setSelectedReportForOCR(null)}
          reportId={selectedReportForOCR.report_id}
          reportFileName={selectedReportForOCR.file_name}
          onStatusUpdated={loadReports}
        />
      )}

      {/* AI Explanation Modal */}
      {selectedReportForAI && (
        <AIExplanationModal
          isOpen={!!selectedReportForAI}
          onClose={() => setSelectedReportForAI(null)}
          reportId={selectedReportForAI.report_id}
          reportFileName={selectedReportForAI.file_name}
        />
      )}

      {/* RAG Query Modal */}
      {selectedReportForRAG && (
        <RAGQueryModal
          isOpen={!!selectedReportForRAG}
          onClose={() => setSelectedReportForRAG(null)}
          reportId={selectedReportForRAG.report_id}
          reportFileName={selectedReportForRAG.file_name}
        />
      )}
    </div>
  )
}


