import { useState, useEffect } from 'react'
import {
  Activity,
  FileText,
  Brain,
  Shield,
  Stethoscope,
  Pill,
  CheckCircle2,
  Server,
  Layers,
  Sparkles,
  ArrowRight
} from 'lucide-react'
import axios from 'axios'

interface HealthStatus {
  status: string
  service: string
  database: string
  version: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [_error, setError] = useState<string | null>(null)


  const checkBackendHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.get<HealthStatus>('http://localhost:8000/api/health', {
        timeout: 3000
      })
      setHealth(res.data)
    } catch {
      setError('Backend API offline or still initializing')
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkBackendHealth()
  }, [])

  const modules = [
    {
      title: 'OCR & Document Processing',
      description: 'Extract raw text, numerical values, and reference ranges from medical PDF/Image lab reports.',
      icon: FileText,
      color: 'from-blue-500 to-cyan-500',
      tag: 'Phase 4'
    },
    {
      title: 'AI Report Explanation',
      description: 'Jargon-free medical report summarization with strict safety disclaimers and parameter breakdown.',
      icon: Brain,
      color: 'from-cyan-500 to-teal-500',
      tag: 'Phase 5'
    },
    {
      title: 'Report-Grounded RAG Q&A',
      description: 'Vector-retrieval grounded Q&A with citations strictly bound to the patient\'s uploaded report.',
      icon: Sparkles,
      color: 'from-indigo-500 to-purple-500',
      tag: 'Phase 6'
    },
    {
      title: 'Symptom Assistant & Triage',
      description: 'Educational symptom guidance with automated red-flag triage and safety warnings.',
      icon: Stethoscope,
      color: 'from-emerald-500 to-teal-500',
      tag: 'Phase 7'
    },
    {
      title: 'Medications & Appointments',
      description: 'Schedule regimens, log dosages, track doctor consultations, and receive reminders.',
      icon: Pill,
      color: 'from-amber-500 to-rose-500',
      tag: 'Phase 8'
    },
    {
      title: 'Security & Access Control',
      description: 'OWASP-aligned JWT authentication, IDOR cross-user protection, and audit logging.',
      icon: Shield,
      color: 'from-rose-500 to-red-500',
      tag: 'Phase 10'
    }
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                MediLens AI
              </span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-400">
                SRS v1.0
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              <Server className="h-3.5 w-3.5 text-slate-400" />
              <span>Backend Status:</span>
              {loading ? (
                <span className="text-amber-400 animate-pulse">Checking...</span>
              ) : health?.status === 'online' ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping inline-block"></span>
                  Online ({health.database})
                </span>
              ) : (
                <span className="text-rose-400 cursor-pointer" onClick={checkBackendHealth} title="Click to retry">
                  Offline (Click retry)
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-12 flex flex-col justify-center">
        <div className="text-center max-w-3xl mx-auto space-y-5">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
            <Layers className="h-3.5 w-3.5" />
            <span>Phase 1 — Foundation & Architecture Baseline</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            AI-Powered Healthcare & <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
              Medical Report Assistant
            </span>
          </h1>

          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            A secure full-stack clinical intelligence platform built according to the final baseline SRS. 
            Automated OCR extraction, grounded RAG Q&amp;A, and patient health tracking.
          </p>

          {/* Quick Action Badges */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" /> PostgreSQL &amp; SQLAlchemy Schema Ready
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" /> FastAPI Modular Architecture Initialized
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" /> React 18 + TypeScript + Tailwind v4 Active
            </span>
          </div>
        </div>

        {/* Modular Architecture Grid */}
        <div className="mt-16">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white">System Architecture &amp; Core Modules</h2>
              <p className="text-sm text-slate-400">Traceable directly to MediLens SRS Sections 6 through 15</p>
            </div>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-sm text-cyan-400 hover:text-cyan-300 font-medium transition"
            >
              Interactive Swagger Docs <ArrowRight className="h-4 w-4" />
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {modules.map((mod, idx) => {
              const Icon = mod.icon
              return (
                <div
                  key={idx}
                  className="group relative rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 backdrop-blur-sm transition-all duration-300 hover:border-slate-700 hover:bg-slate-900/80 hover:shadow-xl hover:shadow-cyan-500/5"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className={`h-11 w-11 rounded-xl bg-gradient-to-tr ${mod.color} flex items-center justify-center shadow-md`}>
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 border border-slate-700/50">
                      {mod.tag}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                    {mod.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {mod.description}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>MediLens AI &bull; B.Tech Final-Year Project Implementation Baseline &bull; Version 1.0</p>
      </footer>
    </div>
  )
}
