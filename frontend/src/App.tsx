import { useState, useEffect } from 'react'
import {
  Activity,
  FileText,
  Brain,
  Shield,
  Stethoscope,
  CheckCircle2,
  Server,
  Sparkles,
  ArrowRight,
  User,
  LogIn,
  UploadCloud,
  FolderOpen
} from 'lucide-react'
import axios from 'axios'
import { authService, type UserSummary } from './services/auth'
import { AuthModal } from './components/auth/AuthModal'
import { ProfileModal } from './components/auth/ProfileModal'
import { ReportUploadCard } from './components/reports/ReportUploadCard'
import { ReportsList } from './components/reports/ReportsList'

interface HealthStatus {
  status: string
  service: string
  database: string
  version: string
}

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loadingHealth, setLoadingHealth] = useState<boolean>(true)
  
  // Authentication states
  const [currentUser, setCurrentUser] = useState<UserSummary | null>(null)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState<boolean>(false)

  // Reports state
  const [reportsRefresh, setReportsRefresh] = useState<number>(0)
  const [activeTab, setActiveTab] = useState<'workspace' | 'architecture'>('workspace')

  const checkBackendHealth = async () => {
    setLoadingHealth(true)
    try {
      const res = await axios.get<HealthStatus>('http://localhost:8000/api/health', {
        timeout: 3000
      })
      setHealth(res.data)
    } catch {
      setHealth(null)
    } finally {
      setLoadingHealth(false)
    }
  }

  const checkCurrentUser = async () => {
    if (authService.isAuthenticated()) {
      try {
        const user = await authService.getMe()
        setCurrentUser(user)
      } catch {
        authService.logout()
        setCurrentUser(null)
      }
    } else {
      setCurrentUser(authService.getStoredUser())
    }
  }

  useEffect(() => {
    checkBackendHealth()
    checkCurrentUser()
  }, [])

  const modules = [
    {
      title: 'User Authentication & RBAC',
      description: 'OWASP-aligned JWT auth, bcrypt password hashing, and role-based permissions (Patient & Admin).',
      icon: Shield,
      color: 'from-emerald-500 to-teal-500',
      tag: 'Phase 2 (Completed)'
    },
    {
      title: 'Reports Management & Storage',
      description: 'Secure multi-tenant file upload, magic byte validation, and authoritative source preservation.',
      icon: UploadCloud,
      color: 'from-blue-500 to-cyan-500',
      tag: 'Phase 3 (Active)'
    },
    {
      title: 'OCR & Document Processing',
      description: 'Extract raw text, numerical values, and reference ranges from medical PDF/Image lab reports.',
      icon: FileText,
      color: 'from-cyan-500 to-teal-500',
      tag: 'Phase 4'
    },
    {
      title: 'AI Report Explanation',
      description: 'Jargon-free medical report summarization with strict safety disclaimers and parameter breakdown.',
      icon: Brain,
      color: 'from-teal-500 to-emerald-500',
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
      title: 'Symptom Assistant & Health Tracking',
      description: 'Educational symptom guidance, medication schedules, and doctor appointment management.',
      icon: Stethoscope,
      color: 'from-amber-500 to-rose-500',
      tag: 'Phase 7 & 8'
    }
  ]

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
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
                Phase 3
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* View Switcher if Authenticated */}
            {currentUser && (
              <div className="hidden md:flex rounded-lg bg-slate-950/80 p-1 border border-slate-800">
                <button
                  onClick={() => setActiveTab('workspace')}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                    activeTab === 'workspace'
                      ? 'bg-cyan-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Reports Workspace
                </button>
                <button
                  onClick={() => setActiveTab('architecture')}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition ${
                    activeTab === 'architecture'
                      ? 'bg-cyan-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Architecture Map
                </button>
              </div>
            )}

            {/* Backend Health Pill */}
            <div className="hidden sm:flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
              <Server className="h-3.5 w-3.5 text-slate-400" />
              <span>Backend:</span>
              {loadingHealth ? (
                <span className="text-amber-400 animate-pulse">Checking...</span>
              ) : health?.status === 'online' ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 inline-block"></span>
                  Online ({health.database})
                </span>
              ) : (
                <span className="text-rose-400 cursor-pointer" onClick={checkBackendHealth} title="Click to retry">
                  Offline
                </span>
              )}
            </div>

            {/* Auth Button or User Badge */}
            {currentUser ? (
              <button
                onClick={() => setIsProfileModalOpen(true)}
                className="flex items-center space-x-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 text-xs font-medium text-white hover:border-cyan-500/50 hover:bg-slate-800 transition shadow-sm cursor-pointer"
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-[11px] font-bold text-white">
                  {currentUser.name.charAt(0).toUpperCase()}
                </div>
                <span>{currentUser.name.split(' ')[0]}</span>
                <span className={`px-1.5 py-0.2 text-[10px] font-semibold rounded ${
                  currentUser.role === 'admin'
                    ? 'bg-rose-950 text-rose-400 border border-rose-800/40'
                    : 'bg-cyan-950 text-cyan-400 border border-cyan-800/40'
                }`}>
                  {currentUser.role.toUpperCase()}
                </span>
              </button>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center space-x-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 px-3.5 py-1.5 text-xs font-semibold text-white shadow-md shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition cursor-pointer"
              >
                <LogIn className="h-3.5 w-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-6 py-10 flex flex-col justify-start w-full">
        {/* Banner Section */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold uppercase tracking-wider">
            <UploadCloud className="h-3.5 w-3.5" />
            <span>Phase 3 — Medical Report Ingestion &amp; Storage Engine</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Clinical Lab Reports &amp; <br />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-500 bg-clip-text text-transparent">
              Secure Document Management
            </span>
          </h1>

          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Multi-tenant document upload pipeline with strict magic byte validation, 
            authoritative source preservation, and BOLA IDOR isolation.
          </p>

          {/* Quick Action Badges */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-1">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> MIME Magic Byte Validation
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Isolated Multi-Tenant Storage
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Authoritative Source Invariant
            </span>
          </div>
        </div>

        {/* Dynamic Content based on User State and Active Tab */}
        {currentUser && activeTab === 'workspace' ? (
          <div className="space-y-8 animate-fade-in">
            {/* Report Upload Component */}
            <ReportUploadCard
              onUploadSuccess={() => {
                setReportsRefresh((prev) => prev + 1)
              }}
            />

            {/* Reports List Table */}
            <ReportsList
              refreshTrigger={reportsRefresh}
              onReportDeleted={() => setReportsRefresh((prev) => prev + 1)}
            />
          </div>
        ) : (
          <div className="space-y-12">
            {!currentUser && (
              <div className="rounded-2xl border border-cyan-500/30 bg-cyan-950/20 p-8 text-center max-w-2xl mx-auto space-y-4">
                <FolderOpen className="h-10 w-10 text-cyan-400 mx-auto" />
                <h3 className="text-lg font-bold text-white">Sign In to Access Clinical Storage</h3>
                <p className="text-xs text-slate-400">
                  Each patient's lab reports are stored in an isolated tenant partition. Sign in or register to test the live upload pipeline.
                </p>
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-2.5 text-xs font-semibold text-white shadow-lg shadow-cyan-500/20 hover:from-cyan-400 hover:to-blue-500 transition cursor-pointer"
                >
                  <User className="h-4 w-4" /> Sign In or Register to Upload
                </button>
              </div>
            )}

            {/* Modular Architecture Grid */}
            <div>
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
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>MediLens AI &bull; B.Tech Final-Year Project Implementation &bull; Version 1.0</p>
      </footer>

      {/* Modals */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user)
          setIsAuthModalOpen(false)
        }}
      />

      {currentUser && (
        <ProfileModal
          isOpen={isProfileModalOpen}
          onClose={() => setIsProfileModalOpen(false)}
          user={currentUser}
          onLogout={() => {
            authService.logout()
            setCurrentUser(null)
          }}
          onUserUpdated={(updated) => setCurrentUser(updated)}
        />
      )}
    </div>
  )
}
