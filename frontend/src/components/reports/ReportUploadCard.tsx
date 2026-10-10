import React, { useState, useRef } from 'react'
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { reportsService, type ReportItem } from '../../services/reports'

interface ReportUploadCardProps {
  onUploadSuccess: (report: ReportItem) => void
}

const CLINICAL_CATEGORIES = [
  'CBC (Complete Blood Count)',
  'Lipid Profile',
  'Blood Glucose / HbA1c',
  'Thyroid Profile (TSH / T3 / T4)',
  'Liver Function Test (LFT)',
  'Kidney Function Test (KFT)',
  'Urinalysis',
  'Other Clinical Document'
]

export const ReportUploadCard: React.FC<ReportUploadCardProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [category, setCategory] = useState<string>('CBC (Complete Blood Count)')
  const [uploading, setUploading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState<boolean>(false)

  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleFileSelect = (file: File) => {
    setError(null)
    setSuccess(null)

    // Client-side quick validation
    const allowed = ['.pdf', '.png', '.jpg', '.jpeg']
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
    if (!allowed.includes(ext)) {
      setError(`Unsupported file type. Please upload a PDF, PNG, or JPG document.`)
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setError(`File size exceeds 10MB limit. Please upload a smaller file.`)
      return
    }

    setSelectedFile(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedFile) {
      setError('Please choose or drop a medical report to upload.')
      return
    }

    setError(null)
    setUploading(true)

    try {
      const cleanCategory = category.split(' (')[0]
      const report = await reportsService.uploadReport(selectedFile, cleanCategory)
      setSuccess(`Report "${selectedFile.name}" ingested successfully!`)
      setSelectedFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      onUploadSuccess(report)
      setTimeout(() => setSuccess(null), 4000)
    } catch (err: any) {
      const msg = err.response?.data?.error?.message || 'Failed to upload report. Please verify file integrity.'
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl shadow-cyan-950/5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <UploadCloud className="h-5 w-5 text-cyan-400" /> Upload Medical Lab Report
          </h3>
          <p className="text-xs text-slate-400">
            Secure, encrypted multi-tenant ingestion for clinical documents.
          </p>
        </div>
        <span className="text-[11px] font-semibold px-2.5 py-1 rounded-md bg-cyan-950 border border-cyan-800/60 text-cyan-400">
          PDF / PNG / JPG &bull; Max 10MB
        </span>
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-rose-500/30 bg-rose-950/40 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-4 flex items-center gap-2.5 rounded-xl border border-emerald-500/30 bg-emerald-950/40 p-3 text-xs text-emerald-300">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Drop Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-all ${
            isDragging
              ? 'border-cyan-400 bg-cyan-950/30'
              : selectedFile
              ? 'border-emerald-500/50 bg-emerald-950/10'
              : 'border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-900/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            className="hidden"
          />

          {selectedFile ? (
            <div className="flex items-center justify-center space-x-3 text-left">
              <div className="h-10 w-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{selectedFile.name}</p>
                <p className="text-xs text-slate-400">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB &bull; Ready for secure upload
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <UploadCloud className="mx-auto h-8 w-8 text-slate-500" />
              <p className="text-sm font-medium text-slate-300">
                Drag and drop your medical lab report, or <span className="text-cyan-400">browse</span>
              </p>
              <p className="text-[11px] text-slate-500">
                Original document is strictly preserved as the authoritative source
              </p>
            </div>
          )}
        </div>

        {/* Category Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Clinical Report Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            >
              {CLINICAL_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 py-2.5 text-xs font-semibold text-white shadow-md shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-40 transition cursor-pointer"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Ingesting &amp; Validating...</span>
                </>
              ) : (
                <span>Upload Report to Secure Storage</span>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
