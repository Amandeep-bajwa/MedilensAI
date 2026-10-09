# MediLens AI — Phase 1 Implementation Document

## 1. Executive Summary & Objective
Phase 1 establishes the foundational engineering baseline for the **MediLens AI** platform (a full-stack clinical document intelligence and personal healthcare management system). The primary objective was to configure a robust, decoupled, and production-ready architecture across the backend, frontend, database, and container orchestration layers, ensuring zero structural refactoring in subsequent phases.

---

## 2. Architectural Decisions & Rationale

### 2.1 Backend Framework: FastAPI (Python 3.11+)
- **Choice**: FastAPI with Uvicorn.
- **Why this was chosen over Django / Flask**:
  - **Asynchronous Native Throughput**: Vital for handling long-polling and I/O-bound tasks in medical document processing (OCR parsing, document chunking, LLM streaming, and vector embeddings).
  - **Pydantic v2 Contract Validation**: Enforces strict payload validation, serialization, and automatic OpenAPI (Swagger / ReDoc) schema generation without additional tooling.
  - **Dependency Injection System**: Allows composable authentication guards, database session lifecycles, and role-based permissions directly into route handlers.

### 2.2 Database Layer: PostgreSQL 16 & SQLAlchemy 2.0
- **Choice**: PostgreSQL 16 (via `psycopg2-binary`) orchestrated with SQLAlchemy 2.0 declarative models and initial DDL scripting.
- **Why this was chosen over MongoDB / DocumentDB**:
  - **Strict Relational Guarantees**: Clinical healthcare data (users, lab reports, ocr extractions, medications, doctor consultations) requires rigid relational integrity, foreign key cascading, and ACID transactions.
  - **Multi-Tenant Data Isolation (BOLA / IDOR Defense)**: Enforcing tenant isolation (`WHERE user_id = :current_user_id`) is native and deterministic in SQL with indexed foreign keys.
  - **Future Extension with `pgvector`**: PostgreSQL natively supports vector embeddings for Retrieval-Augmented Generation (RAG) through the `pgvector` extension, eliminating the immediate need for a separate vector database cluster.

### 2.3 Frontend Framework: React 18, TypeScript, Tailwind CSS, Vite
- **Choice**: Single-Page Application (SPA) built with React 18, TypeScript, Tailwind CSS, and Vite.
- **Why this was chosen over Next.js (SSR) or Vanilla JS**:
  - **Client-Side Document Viewing & Annotation**: Medical report dashboards require high client interactivity (canvas viewing, bounding-box highlights, responsive form interactions).
  - **Strict Type Safety**: TypeScript interfaces ensure end-to-end type parity with backend Pydantic schemas, reducing runtime bugs.
  - **Rapid Build Performance**: Vite provides near-instantaneous Hot Module Replacement (HMR) and optimized rollup production bundles.

### 2.4 Multi-Container Orchestration: Docker & Docker Compose
- **Choice**: Docker Compose defining isolated `db`, `backend`, and `frontend` services with automated dependency resolution.
- **Why this was chosen**:
  - **Reproducibility**: Guarantees identical execution across all development and production environments.
  - **Automated Initialization**: PostgreSQL container automatically executes `database/schema.sql` on first initialization via Docker's entrypoint volume.
  - **Healthchecks**: Backend waits for PostgreSQL readiness check (`pg_isready -U postgres -d medilens_db`) before booting, preventing database connection crashes.

---

## 3. Step-by-Step Implementation Chronology

### Step 1: Environment Isolation & Dependency Manifests
1. Configured `.env.example` documenting all configuration keys:
   - Application mode (`ENVIRONMENT`, `DEBUG`, `PORT`).
   - Database connection string (`DATABASE_URL`).
   - JWT authentication parameters (`SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`).
   - OCR engine parameters (`TESSERACT_CMD`, `POPPLER_PATH`).
   - LLM service provider credentials (`LLM_PROVIDER`, `GEMINI_API_KEY`).
2. Configured `backend/requirements.txt` with locked versions for FastAPI, Uvicorn, SQLAlchemy, Psycopg2, Pydantic, Python-Jose, Passlib/Bcrypt, and Pytest.

### Step 2: Core Engine & Unified Error Handling
1. **Config Management (`backend/app/core/config.py`)**:
   - Implemented `pydantic-settings` `Settings` class with automated `.env` file parsing and fallback defaults.
2. **Database Engine (`backend/app/core/database.py`)**:
   - Configured SQLAlchemy engine with connection pool recycling and a thread-safe `get_db` generator for dependency injection.
3. **Security Primitives (`backend/app/core/security.py`)**:
   - Implemented `get_password_hash` using bcrypt.
   - Implemented `verify_password` for constant-time comparison.
   - Implemented `create_access_token` and `decode_access_token` utilizing HMAC-SHA256 (`HS256`).
4. **Standardized Exception Handling (`backend/app/core/errors.py`)**:
   - Built custom `AppException` class with typed error codes (`code`, `message`, `status_code`).
   - Added global exception handlers for `AppException`, `RequestValidationError`, and unexpected exceptions ensuring RFC-compliant JSON responses.

### Step 3: Domain Models & Relational Schema
1. Implemented complete SQLAlchemy 2.0 models across 10 tables in `backend/app/models/entities.py`:
   - `User` (UUID primary key, email unique index, hashed password, role, timestamps).
   - `Report` (file metadata, processing status enum, cascade deletion).
   - `OCR` (1-to-1 unique mapping to reports, confidence score, text).
   - `ReportChunk` (text chunks, page numbers, embedding vector references).
   - `AIInteraction` (Q&A dialog, report reference, timestamps).
   - `SymptomInteraction` (patient symptom inquiry & educational triage response).
   - `Medication` (dosage, frequency, date ranges).
   - `Appointment` (doctor, specialization, status, datetime).
   - `AuditLog` (event types, success/failure status, structured JSON metadata).
2. Authored relational SQL DDL in `database/schema.sql` with indices on frequently queried foreign keys (`user_id`, `report_id`, `timestamp`).

### Step 4: Application Lifecycle & Health Probes
1. Implemented FastAPI `lifespan` handler in `backend/app/main.py`:
   - Pre-creates local upload directory on startup.
   - Triggers `Base.metadata.create_all` for safe table creation.
2. Implemented `backend/app/api/routes/health.py`:
   - Verifies backend server availability.
   - Executes live database ping (`SELECT 1`) to verify database connectivity.
3. Created unit test suite in `tests/test_foundation.py` covering:
   - Root endpoint response.
   - Health check with live database status.
   - Bcrypt hashing & verification idempotency.
   - JWT encoding and payload recovery.

### Step 5: Container Orchestration & Dockerization
1. Created `backend/Dockerfile` with Debian slim base, system dependencies (`tesseract-ocr`, `poppler-utils`, `libpq-dev`), and non-root execution setup.
2. Created `docker-compose.yml` defining:
   - `db`: PostgreSQL 16 Alpine with healthcheck.
   - `backend`: FastAPI app with live reload volume mount.
   - `frontend`: Vite React dev server.

### Step 6: Frontend Foundation
1. Initialized React 18 + TypeScript + Vite workspace in `frontend/`.
2. Built responsive foundation UI in `frontend/src/App.tsx` displaying:
   - Real-time backend connectivity indicator querying `/api/health`.
   - Architectural roadmap and modules matching the specification.
   - Modern dark theme typography and responsive layouts.

---

## 4. Verification & Validation Metrics
- **Tests**: All foundation tests in `tests/test_foundation.py` passed with 100% success rate.
- **Health Probe**: Both backend and database confirmed online.
- **Git State**: Clean working tree, `.gitignore` thoroughly configured, and code pushed cleanly to remote repository.
