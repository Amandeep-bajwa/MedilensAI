# MediLens AI

> **AI-Powered Healthcare Symptom & Medical Report Assistant**  
> *Final-Year B.Tech Capstone Project | Baseline SRS v1.0*

---

## 📌 Overview

**MediLens AI** is a secure, full-stack clinical document intelligence and personal healthcare management platform. It allows users to securely upload medical lab reports (PDF/images), extract structured laboratory findings through an OCR pipeline, obtain clear, jargon-free explanations powered by Large Language Models (LLMs), and ask contextually grounded questions using Retrieval-Augmented Generation (RAG).

---

## 🏗️ Project Structure

```text
medilenAI/
├── backend/                  # FastAPI asynchronous backend application
│   ├── app/
│   │   ├── api/              # REST route definitions and auth dependencies
│   │   ├── core/             # Configuration, database engine, security & error handling
│   │   ├── models/           # SQLAlchemy ORM models (SRS Section 8)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   └── services/         # OCR, Storage, AI, RAG business logic
│   ├── Dockerfile            # Container definition for backend
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Application views (Dashboard, Reports, AI, Health)
│   │   └── services/         # Axios API client integrations
│   ├── Dockerfile            # Container definition for frontend
│   └── vite.config.ts        # Vite build & Tailwind configuration
│
├── database/                 # Database migrations and seed scripts
├── docs/                     # SRS specification, Architecture diagrams & ER schema
├── docker-compose.yml        # Multi-container orchestration (DB + API + Web)
├── .env.example              # Environment variables template
└── README.md
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+ & npm**
- **Docker & Docker Compose** (optional for containerized run)

### 2. Backend Setup
```bash
# Setup virtual environment
python -m venv .venv
# Activate on Windows:
.venv\Scripts\activate
# Activate on macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI Development Server
uvicorn app.main:app --app-dir backend --reload --port 8000
```
- Interactive API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Probe: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

### 4. Running via Docker Compose
```bash
docker compose up --build
```

---

## 🛡️ Medical Safety & Disclaimer
MediLens AI is strictly an **information management and educational assistance system**. It does not provide medical diagnoses, prescribe treatments, or replace certified healthcare professionals.
