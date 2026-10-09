# MediLens AI — Phase 2 Implementation Document

## 1. Executive Summary & Objective
Phase 2 implements the **User Authentication, Role-Based Access Control (RBAC), and Profile Management Module** for MediLens AI. Healthcare platforms require uncompromising security guarantees: sensitive medical documents, health records, and AI interactions must never be exposed across users, and administrative operations must remain strictly guarded.

This implementation delivers an end-to-end authentication ecosystem compliant with **OWASP API Security Top 10** standards, complete with full-stack UI integration and 100% passing automated test coverage.

---

## 2. Architectural Decisions & Engineering Rationale

### 2.1 Stateless JWT (HMAC-SHA256) vs. Stateful Server Sessions
- **Choice**: JSON Web Tokens (JWT) signed via HMAC-SHA256 (`HS256`) with a configurable expiration window (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **Engineering Rationale**:
  - **Horizontal Scalability**: Eliminates session state lookups on Redis or shared session caches, allowing backend worker instances to validate authorization headers independently.
  - **Decoupled Architecture**: Enables seamless consumption across web applications (React SPA), future mobile apps, and microservices without dealing with cross-domain third-party cookie restrictions.
  - **Cryptographic Tamper-Proofing**: Claims (`sub`, `role`, `email`, `exp`) cannot be modified in transit without invalidating the cryptographic signature.

### 2.2 Password Security: Bcrypt Adaptive Hashing
- **Choice**: Bcrypt with automated salt generation via `passlib[bcrypt]` and `bcrypt`.
- **Engineering Rationale**:
  - **Resilience Against Hardware Acceleration**: Bcrypt is intentionally memory- and CPU-intensive, offering strong resistance to GPU/ASIC brute-force dictionary attacks compared to SHA-256 or MD5.
  - **Salting Guarantee**: Prevents rainbow table attacks even if two users choose identical passwords.

### 2.3 Dependency Injection RBAC Guard Pattern
- **Choice**: Composable FastAPI dependency factory (`require_role(*allowed_roles)`).
- **Engineering Rationale**:
  - **Fail-Safe Declarative Enforcement**: Route handlers declare their access requirements directly in their signature (e.g., `_admin: User = Depends(require_admin)`). Unauthenticated or unauthorized callers are intercepted before any business logic executes.
  - **Zero Duplication**: Shared logic across routes ensures that inactive or deleted accounts are rejected consistently.

### 2.4 Persistent Healthcare Security Audit Logging
- **Choice**: Synchronous persistence into the `audit_logs` table via `record_audit_log`.
- **Engineering Rationale**:
  - **Regulatory Compliance (HIPAA / GDPR / SRS Section 8)**: Any clinical or identity-related security event (`AUTH_REGISTER`, `AUTH_LOGIN`, `AUTH_PASSWORD_CHANGE`, `ADMIN_UPDATE_USER_STATUS`) is recorded with an immutable timestamp, user identifier, status (`Success` / `Failure`), and structured JSON metadata.
  - **Non-Repudiation**: Guarantees traceability for suspicious login attempts or unauthorized access patterns.

### 2.5 Frontend Token Interceptor Architecture
- **Choice**: Axios request and response interceptors.
- **Engineering Rationale**:
  - **Transparent Authorization**: The Bearer token is automatically attached to outgoing requests without requiring manual prop drilling.
  - **Self-Healing on Token Expiration**: Catches `401 Unauthorized` responses globally, purging stale tokens and returning the user to an unauthenticated state gracefully.

---

## 3. Step-by-Step Implementation Record

### Step 1: Pydantic Validation Contracts
1. **`backend/app/schemas/auth.py`**:
   - `UserRegisterRequest`: Validates full name length (2–100 chars), strict RFC-compliant email formatting via `EmailStr`, password complexity (minimum 8 characters), and role assignment.
   - `UserLoginRequest`: Sanitizes incoming credentials.
   - `TokenResponse`: Returns standard Bearer token envelope, expiration seconds, and serialized user summary.
   - `PasswordChangeRequest`: Enforces current password verification and minimum 8-character new password constraint.
2. **`backend/app/schemas/user.py`**:
   - `UserProfileResponse`: Extends user information with live aggregated counts (`total_reports`, `total_medications`, `total_appointments`).
   - `UserProfileUpdateRequest`: Handles profile mutation.
   - `UserStatusUpdateRequest`: Administrative schema for account activation and role toggles.

### Step 2: Audit Logging Subsystem
- **`backend/app/services/audit.py`**:
  - Implemented `record_audit_log()` helper to persist auditable events with structured JSON metadata into the database.

### Step 3: RBAC Dependency Factory
- **`backend/app/api/deps.py`**:
  - `get_current_user`: Resolves JWT claims, queries database for active account, raises `401` or `403` accordingly.
  - `require_role(*allowed_roles)`: Parametric factory returning role validators (`require_admin`, `require_active_user`).

### Step 4: Authentication Route Handlers
- **`backend/app/api/routes/auth.py`**:
  - `POST /api/auth/register`: Duplicate email collision check (`409 Conflict`), password hashing, audit log entry, and instant JWT generation.
  - `POST /api/auth/login`: Constant-time password comparison, audit logging for both successful and failed attempts, and JWT issuance.
  - `GET /api/auth/me`: Resolves current authenticated session.
  - `POST /api/auth/change-password`: Verifies current password, prohibits reuse of identical password, hashes new secret, and emits audit event.

### Step 5: User & Administrative Route Handlers
- **`backend/app/api/routes/users.py`**:
  - `GET /api/users/profile`: Aggregates active reports, medications, and appointment records for the caller.
  - `PUT /api/users/profile`: Name mutation with audit record.
  - `GET /api/users/`: Paginated and searchable account listing (restricted to `admin`).
  - `PATCH /api/users/{user_id}/status`: Administrative user promotion and account activation (with safeguards prohibiting self-deactivation).

### Step 6: Frontend Client Integration
1. **`frontend/src/services/api.ts`**: Configured Axios client with Bearer token injection and auto-logout on `401`.
2. **`frontend/src/services/auth.ts`**: Typed client methods for all authentication endpoints.
3. **`frontend/src/components/auth/AuthModal.tsx`**: Responsive modal supporting Sign In and Registration workflows with validation feedback.
4. **`frontend/src/components/auth/ProfileModal.tsx`**: Account management drawer displaying live aggregated metrics, profile editing, password changing, and sign-out controls.
5. **`frontend/src/App.tsx`**: Integrated user badge in navigation header, authentication trigger banner, and module status display.

---

## 4. OWASP API Security Alignment

| OWASP Category | Threat Prevented | Phase 2 Mitigation Implemented |
| :--- | :--- | :--- |
| **API1: BOLA** | Cross-user data harvesting | User profiles and credentials always scoped to `current_user.user_id`. |
| **API2: Broken Authentication** | Credential stuffing, weak tokens | Bcrypt password hashing, signed JWT with expiration, constant-time checks. |
| **API3: Broken Object Property Level Auth** | Role self-elevation | Normal users cannot pass admin role overrides; only admins can promote via dedicated PATCH route. |
| **API5: Broken Function Level Auth** | Unauthorized access to admin routes | `require_admin` dependency halts execution with 403 on non-admin calls. |
| **API8: Security Misconfiguration** | Verbose error disclosures | Unified `AppException` handles errors without leaking SQL statements or stack traces. |
| **API10: Unsafe Consumption of APIs** | Lack of auditability | Persistent `AuditLog` entries for every login, failure, and administrative status change. |

---

## 5. Verification & Test Metrics

### Automated Backend Tests (`pytest -v tests`)
- `test_user_registration_success`: **PASSED**
- `test_user_registration_duplicate_email`: **PASSED** (409 Conflict)
- `test_login_success_and_failure`: **PASSED** (200 OK & 401 Unauthorized)
- `test_auth_me_endpoint`: **PASSED** (Bearer token validation)
- `test_password_change_flow`: **PASSED** (Verification, hash rotation, old token rejection)
- `test_rbac_admin_protection`: **PASSED** (403 Forbidden for standard user, 200 OK for admin)
- `test_user_profile_crud`: **PASSED** (Aggregated counts and update)
- **Foundation Suite**: All 4 foundation tests **PASSED**
- **Total Backend Coverage**: **11 of 11 tests passed (100%)**

### Frontend TypeScript Build (`tsc -b && vite build`)
- **Compilation**: 0 errors, 0 warnings.
- **Production Asset Bundle**: Generated cleanly in 2.52s.
