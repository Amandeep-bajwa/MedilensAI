# MediLens AI - System Architecture Specification

## 1. High-Level Architecture (SRS Section 14)

MediLens AI utilizes a modular, layered client-server architecture designed for high maintainability, testability, and data isolation.

```mermaid
graph TD
    subgraph Client [Presentation Layer]
        Browser[User Browser]
        ReactApp[React 18 + TypeScript + Vite + Tailwind CSS]
        Browser --> ReactApp
    end

    subgraph API [API & Gateway Layer]
        FastAPI[FastAPI Asynchronous Gateway]
        CORS[CORS & Rate Limiter / SlowAPI]
        AuthGuard[JWT Auth & RBAC Middleware]
        ReactApp -- HTTPS / REST (JSON) --> CORS
        CORS --> AuthGuard
        AuthGuard --> FastAPI
    end

    subgraph Modules [Business Logic Modules - SRS Sec 14.2]
        M_Auth[Auth & Users Module]
        M_Reports[Reports Management Module]
        M_OCR[OCR & Text Cleaning Engine]
        M_AI[AI Report Explanation Module]
        M_RAG[RAG Retrieval Engine]
        M_Symptoms[Symptom Assistant & Triage]
        M_Health[Medications & Appointments]
        M_Audit[Audit Logging & Security]

        FastAPI --> M_Auth
        FastAPI --> M_Reports
        FastAPI --> M_OCR
        FastAPI --> M_AI
        FastAPI --> M_RAG
        FastAPI --> M_Symptoms
        FastAPI --> M_Health
        FastAPI --> M_Audit
    end

    subgraph Data [Data Persistence & External Services]
        PG[(PostgreSQL Database)]
        VectStore[(Vector Store - pgvector / Chroma)]
        Disk[Secure Local File Storage /uploads]
        LLM[External LLM Service - Gemini / OpenAI]
        OCR_Engine[Tesseract OCR / PDF Parser]

        M_Auth --> PG
        M_Reports --> PG
        M_Reports --> Disk
        M_OCR --> OCR_Engine
        M_RAG --> VectStore
        M_AI --> LLM
        M_RAG --> LLM
        M_Health --> PG
        M_Audit --> PG
    end
```

## 2. Security Boundaries & Invariants
- **BOLA / IDOR Defense**: All database queries enforce strict user tenant isolation: `user_id == current_user.user_id`.
- **Authoritative Source Invariant**: Uploaded original medical documents are never modified or overwritten by OCR/AI pipelines.
- **Safety Boundary**: The AI engine explicitly declines clinical diagnosis or medication modifications, attaching mandatory healthcare disclaimers.
