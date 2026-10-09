-- =============================================================================
-- MediLens AI - Complete Database Schema (PostgreSQL 16)
-- SRS Reference: Section 8 (Data Requirements) & Appendix B
-- =============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. USERS TABLE (SRS 8.1)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. REPORTS TABLE (SRS 8.2)
CREATE TABLE IF NOT EXISTS reports (
    report_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'Other',
    processing_status VARCHAR(30) NOT NULL DEFAULT 'Uploaded',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
CREATE INDEX IF NOT EXISTS idx_reports_uploaded_at ON reports(uploaded_at);

-- 3. OCR RECORDS TABLE (SRS 8.3)
CREATE TABLE IF NOT EXISTS ocr_records (
    ocr_id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) UNIQUE NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    extracted_text TEXT,
    confidence REAL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ocr_report_id ON ocr_records(report_id);

-- 4. REPORT CHUNKS TABLE (SRS 8.4)
CREATE TABLE IF NOT EXISTS report_chunks (
    chunk_id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    page_number VARCHAR(20),
    embedding_reference VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_report_id ON report_chunks(report_id);

-- 5. AI INTERACTIONS TABLE (SRS 8.5)
CREATE TABLE IF NOT EXISTS ai_interactions (
    interaction_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    report_id VARCHAR(36) REFERENCES reports(report_id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ai_interactions_user_id ON ai_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_interactions_report_id ON ai_interactions(report_id);

-- 6. SYMPTOM INTERACTIONS TABLE (SRS 8.6)
CREATE TABLE IF NOT EXISTS symptom_interactions (
    interaction_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    symptom_input TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_symptom_interactions_user_id ON symptom_interactions(user_id);

-- 7. MEDICATIONS TABLE (SRS 8.7)
CREATE TABLE IF NOT EXISTS medications (
    medication_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_medications_user_id ON medications(user_id);

-- 8. APPOINTMENTS TABLE (SRS 8.8)
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    doctor_name VARCHAR(150) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(20) NOT NULL,
    location VARCHAR(255),
    notes TEXT,
    status VARCHAR(30) NOT NULL DEFAULT 'Upcoming',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_appointments_user_id ON appointments(user_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);

-- 9. AUDIT LOGS TABLE (SRS 8.9)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    result VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata_info JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
