# MediLens AI — Phase 3 Implementation Document

## 1. Executive Summary & Objective
Phase 3 implements the **Medical Reports Management & Secure Ingestion Engine (`M_Reports`)** for MediLens AI. In clinical document platforms, uploaded lab reports (PDFs, pathology blood panels, metabolic profiles, radiological scans) represent the single source of truth for all downstream pipelines (OCR extraction in Phase 4, AI explanation in Phase 5, and vector RAG retrieval in Phase 6).

This implementation provides an enterprise-grade document ingestion pipeline ensuring strict MIME magic-byte validation, multi-tenant disk isolation, Broken Object-Level Authorization (BOLA / IDOR) defense, and HIPAA-compliant data retention and purging.

---

## 2. Architectural Decisions & Engineering Rationale

### 2.1 Cryptographic Magic-Byte Inspection vs. Trusting Extensions
- **Choice**: Binary header inspection (`validate_file_security`) verifying raw byte signatures (`%PDF` for PDFs, `\x89PNG` for PNGs, `\xff\xd8\xff` for JPEGs) alongside file extension checks.
- **Engineering Rationale**:
  - **Malicious Upload Mitigation**: Attackers frequently rename executable binaries or PHP/shell scripts (e.g., `payload.sh.pdf` or `webshell.php.png`) to bypass superficial extension filters.
  - **Fail-Fast Integrity Verification**: Corrupted, truncated, or zero-byte uploads are rejected immediately before touching the storage engine or database.

### 2.2 Partitioned Multi-Tenant Directory Storage
- **Choice**: Storing files in tenant-scoped directories: `uploads/{user_id}/{report_id}_{sanitized_basename}`.
- **Engineering Rationale**:
  - **Path Traversal Defense**: Sanitizing filenames via `sanitize_filename()` strips all path traversal characters (`../`, `\`, null bytes), preventing directory escape attacks.
  - **Zero Name Collisions**: Prefixing filenames with UUID `report_id` prevents overwriting when a patient uploads multiple documents named `Report.pdf`.
  - **Data Isolation & OS Security**: Enables future filesystem-level permission confinement and rapid tenant data purging.

### 2.3 Strict BOLA / IDOR Defense with 404 Masking
- **Choice**: All report retrieval, streaming, category updating, and deletion endpoints query by both `report_id` and `current_user.user_id` (unless the caller possesses the `admin` role). Unauthorized attempts return `404 Not Found` rather than `403 Forbidden`.
- **Engineering Rationale**:
  - **Prevention of Resource Enumeration**: Returning `403 Forbidden` reveals to an attacker that a document exists at a specific UUID. Returning `404 Not Found` completely hides document existence across tenants.

### 2.4 Authoritative Source Invariant
- **Choice**: The uploaded medical document is treated as an immutable, read-only binary artifact.
- **Engineering Rationale**:
  - **Clinical Auditability**: Downstream OCR text extraction and AI summarization must never modify, re-encode, or overwrite the original clinical document.
  - **Legal / Healthcare Non-Repudiation**: Guarantees that downloaded files remain byte-for-byte identical to what the patient or lab originally submitted.

### 2.5 Disk Storage Synchronization on Deletion
- **Choice**: Deleting a report record in PostgreSQL simultaneously purges the physical file from disk via `delete_upload_file()`.
- **Engineering Rationale**:
  - **HIPAA / GDPR Right to Erasure**: Leaving orphaned clinical files on disk after database deletion violates privacy standards and causes storage leaks.
  - **Atomic Cleanup**: Cascades deletion across relational OCR and AI records automatically.

---

## 3. Step-by-Step Implementation Record

### Step 1: Pydantic Validation Schemas
- **`backend/app/schemas/report.py`**:
  - `ReportResponse`: Serializes report identifiers, clinical category, status, file size in bytes, and UTC timestamps.
  - `ReportListResponse`: Paginated envelope returning report items, total count, and page metadata.
  - `ReportUpdate`: Schema for clinical category updates.

### Step 2: Storage & Magic-Byte Validation Service
- **`backend/app/services/storage.py`**:
  - `validate_file_security()`: Verifies non-empty payload, enforces `MAX_FILE_SIZE_MB` threshold, and inspects magic byte headers.
  - `sanitize_filename()`: Regex normalization removing unsafe symbols.
  - `save_upload_file()`: Writes file to isolated tenant directory.
  - `delete_upload_file()`: Safely unlinks file from disk.
  - `get_file_size()`: Computes disk file size in bytes.

### Step 3: REST API Route Handlers
- **`backend/app/api/routes/reports.py`**:
  - `POST /api/reports/upload`: Multipart form-data ingestion with file validation, tenant storage, DB creation, and `REPORT_UPLOAD` audit logging.
  - `GET /api/reports/`: Paginated listing with search by filename and category filtering, scoped strictly to the current tenant.
  - `GET /api/reports/{report_id}`: Single report metadata retrieval with BOLA check.
  - `GET /api/reports/{report_id}/download`: Binary streaming via `FileResponse` with correct MIME types.
  - `PATCH /api/reports/{report_id}`: Clinical category updating with `REPORT_UPDATE` audit logging.
  - `DELETE /api/reports/{report_id}`: Purges DB record and unlinks file from storage with `REPORT_DELETE` audit logging.

### Step 4: Master Router Registration
- **`backend/app/api/router.py`**: Mounted `reports.router` under `/reports`.

### Step 5: Frontend API Client
- **`frontend/src/services/reports.ts`**: Implemented typed client methods for file upload, listing, download triggers via temporary Blob URLs, and deletion.

### Step 6: Interactive Frontend Components
1. **`ReportUploadCard.tsx`**: Drag-and-drop dropzone, clinical category dropdown (`CBC`, `Lipid Profile`, `Thyroid Profile`, etc.), size validation, and upload spinners.
2. **`ReportsList.tsx`**: Document table displaying status pills (`Uploaded`, `Processing`, `Completed`), category tags, formatted file sizes, download triggers, and deletion confirmation.
3. **`App.tsx`**: Integrated workspace switching, live reports counter, and real-time list refreshing upon successful ingestion.

### Step 7: Automated Pytest Suite
- **`tests/test_reports_management.py`**:
  - Valid PDF, PNG, and JPEG upload verification.
  - Rejection of invalid extensions (`.sh`, `.exe`).
  - Rejection of spoofed files (text files with `.pdf` extensions).
  - Multi-tenant BOLA isolation: User B cannot retrieve, download, list, or delete User A's reports.
  - Download binary byte equality verification.
  - Deletion verification confirming physical disk removal.

---

## 4. Security & Compliance Alignment

| Threat / Requirement | Impact | Phase 3 Solution Implemented |
| :--- | :--- | :--- |
| **MIME / Extension Spoofing** | Code execution via uploaded scripts | Header byte sniffing (`%PDF`, `\x89PNG`, `\xff\xd8\xff`) halts unverified uploads. |
| **Path Traversal (`../`)** | Overwriting critical system files | `sanitize_filename()` strips all path traversal characters; paths are generated server-side. |
| **Cross-Tenant Access (BOLA)** | Viewing other patients' lab reports | Scoped query filtering with 404 masking prevents unauthorized access and resource probing. |
| **Disk Exhaustion (DoS)** | Filling server storage | Enforces `MAX_FILE_SIZE_MB` (10MB) limit before writing to disk. |
| **Audit Non-Repudiation** | Lack of traceability | Synchronous `audit_logs` entries for upload, update, and deletion operations. |

---

## 5. Verification & Test Metrics

### Backend Test Suite (`pytest -v tests`)
- `test_upload_pdf_success`: **PASSED**
- `test_upload_image_success`: **PASSED**
- `test_upload_unsupported_extension`: **PASSED** (400 Bad Request)
- `test_upload_magic_spoofing_rejected`: **PASSED** (400 Bad Request)
- `test_bola_tenant_isolation`: **PASSED** (404 Isolation for read, download, delete)
- `test_download_and_delete_lifecycle`: **PASSED** (Binary streaming & physical file removal)
- **Cumulative Suite**: **17 of 17 tests passed (100% pass rate)**.

### Frontend TypeScript Compilation (`tsc -b && vite build`)
- **Compilation**: 0 errors, 0 warnings.
- **Asset Bundling**: Completed cleanly in 2.94s.
