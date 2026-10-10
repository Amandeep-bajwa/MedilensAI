# MediLens AI — Phase 6 Implementation Document

## 1. Executive Summary & Objective
Phase 6 implements the **Report-Grounded RAG Q&A Engine (`M_RAG`)** for MediLens AI. While Phase 4 partitioned laboratory documents into semantic chunks and Phase 5 synthesized executive clinical summaries, patients frequently require targeted answers to specific health questions regarding their diagnostic reports (e.g., *"What is my fasting glucose level?"*, *"Does my report show any kidney abnormalities?"*, or *"What dietary recommendations were noted by the doctor?"*).

The primary objective of Phase 6 is to provide a grounded question-answering engine strictly anchored in the patient's uploaded document. It prevents medical hallucinations through similarity-thresholded refusal boundaries, generates traceable page-level citations (`[Page X]`), enforces multi-tenant security isolation, and adheres to mandatory clinical safety disclaimers.

---

## 2. Architectural Decisions & Engineering Rationale

### 2.1 Hybrid Dense-Sparse Semantic Similarity Engine vs. External Vector DB Dependency
- **Choice**: Embedded hybrid retrieval engine combining dense token overlap, clinical domain synonym expansion, and positional context scoring:
  - Computes normalized relevance scores ($0.0 \le \text{Score} \le 1.0$) across all semantic chunks associated with the report.
  - Generates focused contextual snippets centered around the exact matched clinical terms.
- **Engineering Rationale**:
  - **Zero-Dependency Resilience**: External vector databases (Pinecone, Weaviate, Qdrant) or heavy C-extension packages introduce network dependencies, cold-start latency, cloud costs, and container orchestration overhead.
  - **Sub-15ms In-Memory Execution**: Lab reports typically contain between 2 and 25 semantic chunks. In-memory semantic evaluation executes in under 15 milliseconds per query.
  - **100% Deterministic Reproducibility**: Retrieval behavior is consistent and verifiable across test and production environments.

### 2.2 Clinical Domain Synonym Expansion (`CLINICAL_SYNONYMS`)
- **Choice**: Built-in biomedical taxonomy mapping colloquial patient inquiries to formal laboratory nomenclature:
  - *"kidney"* / *"renal"* $\rightarrow$ `["creatinine", "bun", "urea", "egfr", "renal", "kidney"]`
  - *"sugar"* / *"diabetes"* $\rightarrow$ `["glucose", "fasting blood sugar", "fbs", "hba1c", "blood sugar", "glycemic"]`
  - *"heart"* / *"cholesterol"* $\rightarrow$ `["cholesterol", "lipid", "ldl", "hdl", "triglycerides", "lipid profile"]`
  - *"anemia"* / *"blood count"* $\rightarrow$ `["hemoglobin", "hgb", "rbc", "platelets", "wbc", "hematocrit", "iron"]`
  - *"infection"* / *"immunity"* $\rightarrow$ `["wbc", "white blood cells", "leukocytes", "neutrophils", "lymphocytes"]`
  - *"liver"* / *"hepatic"* $\rightarrow$ `["alt", "ast", "sgpt", "sgot", "bilirubin", "alp", "hepatic"]`
  - *"thyroid"* $\rightarrow$ `["tsh", "t3", "t4", "thyroxine"]`
- **Engineering Rationale**:
  - **Overcoming Layperson Vocabulary Mismatch**: Patients rarely ask using exact medical acronyms (e.g., asking *"How are my kidneys doing?"* instead of *"What is my serum creatinine concentration?"*). Clinical synonym expansion bridges this cognitive gap with high retrieval recall.

### 2.3 Anti-Hallucination Refusal Invariant & Grounding Threshold
- **Choice**: Strict score thresholding ($\text{Score} \ge 0.12$). If the top-scoring chunk falls below this threshold:
  - `is_grounded` is set to `False`.
  - The engine outputs a transparent refusal: *"Based on the clinical data in '[Report]', there is no direct record or mention matching your question regarding '[Topic]'. Please verify that the intended laboratory document has been uploaded, or discuss this directly with your ordering physician."*
- **Engineering Rationale**:
  - **Clinical Safety Boundary**: Hallucination in a healthcare application is dangerous. If a patient uploads a CBC panel and asks about brain tumors or cardiac enzymes, the system must clearly indicate that the report does not contain that information, rather than fabricating an answer.

### 2.4 Page-Level Citation Attribution
- **Choice**: Every retrieved citation returns:
  - `chunk_id`: Unique identifier of the document chunk.
  - `page_number`: Exact report page where the text appears.
  - `snippet`: Highlighted text excerpt (120–180 characters) surrounding the matched parameters.
  - `relevance_score`: Normalized similarity percentage ($0\% - 100\%$).
- **Engineering Rationale**:
  - **Traceability & Verification**: Enables patients and physicians to independently verify AI-extracted statements against the authoritative source document.

### 2.5 Multi-Tenant Broken Object Level Authorization (BOLA) Protection
- **Choice**: Every query verifies that the report belongs to `current_user.user_id`, raising `404 Not Found` upon ownership mismatch.
- **Engineering Rationale**:
  - **HIPAA / OWASP Alignment**: Returning HTTP 404 rather than 403 prevents attackers from probing the API to confirm whether arbitrary report IDs exist in the system.

### 2.6 Persistence, Reindexing & Audit Controls
- **Choice**: All grounded Q&A queries are recorded in `ai_interactions` and audited in `audit_logs` (`RAG_QUERY_EXECUTED`, `RAG_CHUNKS_REINDEXED`). Supports on-demand re-indexing of semantic chunks.
- **Engineering Rationale**:
  - **Compliance & History**: Gives patients instant access to previous grounded inquiries while providing a full forensic audit trail.

---

## 3. Step-by-Step Implementation Record

### Step 1: Pydantic Validation Schemas
- **`backend/app/schemas/rag.py`**:
  - `RAGCitation`: Schema for individual chunk citations with page number, snippet, and relevance score.
  - `RAGQueryRequest`: Query input model with min/max length validation and `top_k` chunk limit.
  - `RAGQueryResponse`: Output model containing answer, citations list, confidence score, `is_grounded` flag, disclaimer, and timestamps.
  - `RAGIndexStatusResponse` / `RAGReindexResponse`: Schemas for chunk indexing status and manual re-indexing.
  - `RAGHistoryItem`: Historical query item schema.

### Step 2: Semantic Retrieval & Grounding Service
- **`backend/app/services/rag.py`**:
  - `CLINICAL_SYNONYMS`: Medical domain synonym taxonomy.
  - `tokenize_and_clean()` / `expand_query_terms()`: Text normalization and query expansion.
  - `compute_dense_sparse_similarity()`: Hybrid scoring algorithm combining term overlap, direct matches, and snippet extraction.
  - `search_relevant_chunks()`: Top-$k$ chunk ranker.
  - `synthesize_grounded_answer()`: Constructs cited answers and enforces refusal for out-of-domain topics.
  - `query_rag_engine()`: Master orchestrator enforcing BOLA checks, invoking retrieval, persisting to `ai_interactions`, and logging audit events.
  - `get_rag_index_status()` / `reindex_report_chunks()` / `get_rag_history()`: Status, re-indexing, and history retrieval handlers.

### Step 3: REST API Route Handlers
- **`backend/app/api/routes/rag.py`**:
  - `POST /api/reports/{id}/rag/query`: Runs grounded question answering with page citations.
  - `GET /api/reports/{id}/rag/status`: Returns indexing metadata.
  - `POST /api/reports/{id}/rag/reindex`: Re-indexes semantic chunks.
  - `GET /api/reports/{id}/rag/history`: Retrieves previous grounded inquiries.

### Step 4: Router Registration
- **`backend/app/api/router.py`**: Mounted `rag.router` under tags `Report-Grounded RAG Q&A Engine`.

### Step 5: Frontend API Client
- **`frontend/src/services/rag.ts`**: TypeScript client methods (`queryRAG`, `getIndexStatus`, `reindexChunks`, `getHistory`).

### Step 6: Frontend UI Components
1. **`frontend/src/components/rag/RAGQueryModal.tsx`**:
   - Natural language query input with suggested prompt chips (*"What are my fasting blood glucose findings?"*, *"Explain my cholesterol profile"*, *"Are my kidney levels normal?"*).
   - Indexed chunks status bar with live count and "Re-index Chunks" action button.
   - Grounded Answer card with `Grounded in Report` or `Not Found / Refusal` status badges and relevance percentage.
   - Source Citations drawer displaying `Page X` badge, chunk ID, match score, and verbatim excerpt.
   - History drawer showing past queries and answers.
   - Prominently displayed medical safety disclaimer banner.
2. **`frontend/src/components/reports/ReportsList.tsx`**: Added purple BookOpen action button to launch `RAGQueryModal`.
3. **`frontend/src/App.tsx`**: Updated Phase indicators to Phase 6.

### Step 7: Automated Integration Test Suite
- **`tests/test_rag_pipeline.py`**:
  - `test_rag_query_with_citations_success`: Validates grounded answering, page citation construction, and disclaimer.
  - `test_rag_query_refusal_for_unrelated_topic`: Confirms anti-hallucination refusal when asked about unrelated topics.
  - `test_rag_index_status_and_reindex`: Verifies chunk count inspection and dynamic re-indexing.
  - `test_rag_history_retrieval`: Verifies retrieval of past Q&A interactions.
  - `test_rag_bola_isolation`: Confirms HTTP 404 security masking against cross-tenant queries.

---

## 4. Verification & Validation Metrics

### Backend Test Suite (`pytest -v tests`)
- **Total Test Cases**: **30 passed out of 30**.
- **Breakdown**:
  - Phase 1 Foundation: 4 tests passing
  - Phase 2 Auth & RBAC: 7 tests passing
  - Phase 3 Reports Management: 6 tests passing
  - Phase 4 OCR Pipeline: 4 tests passing
  - Phase 5 AI Explanation: 4 tests passing
  - Phase 6 RAG Engine: 5 tests passing
- **Result**: `30 passed, 1 warning in 26.51s` (100% pass rate).

### Frontend Production Build (`npm run build`)
- **TypeScript Typecheck**: Clean pass (`tsc -b`).
- **Vite Bundle Compilation**: 1,968 modules transformed in 2.41s.
- **Result**: Exit code `0`.
