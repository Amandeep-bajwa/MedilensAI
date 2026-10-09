# MediLens AI - Entity Relationship (ER) Diagram

Based on **SRS Section 8 & Appendix B**, this diagram models the relational entities, primary keys, foreign keys, and cascading relationships for the MediLens AI platform.

```mermaid
erDiagram
    USERS ||--o{ REPORTS : owns
    USERS ||--o{ MEDICATIONS : tracks
    USERS ||--o{ APPOINTMENTS : schedules
    USERS ||--o{ AI_INTERACTIONS : initiates
    USERS ||--o{ SYMPTOM_INTERACTIONS : logs
    USERS ||--o{ AUDIT_LOGS : generates
    
    REPORTS ||--o| OCR_RECORDS : extracts
    REPORTS ||--o{ REPORT_CHUNKS : splits_into
    REPORTS ||--o{ AI_INTERACTIONS : references

    USERS {
        string user_id PK "UUID"
        string name
        string email UK
        string password_hash
        string role "user | admin"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    REPORTS {
        string report_id PK "UUID"
        string user_id FK "Owner"
        string file_name
        string file_type "pdf | png | jpg | jpeg"
        string file_path
        string category "CBC | Blood Test | Lipid Profile | etc."
        string processing_status "Uploaded | Processing | Completed | Failed"
        datetime uploaded_at
        datetime updated_at
    }

    OCR_RECORDS {
        string ocr_id PK "UUID"
        string report_id FK "1-to-1 unique"
        text extracted_text
        float confidence
        string status "Pending | Completed | Failed"
        datetime created_at
    }

    REPORT_CHUNKS {
        string chunk_id PK "UUID"
        string report_id FK
        text chunk_text
        string page_number
        string embedding_reference
        datetime created_at
    }

    AI_INTERACTIONS {
        string interaction_id PK "UUID"
        string user_id FK
        string report_id FK "Nullable"
        text question
        text response
        datetime created_at
    }

    SYMPTOM_INTERACTIONS {
        string interaction_id PK "UUID"
        string user_id FK
        text symptom_input
        text response
        datetime created_at
    }

    MEDICATIONS {
        string medication_id PK "UUID"
        string user_id FK
        string medicine_name
        string dosage
        string frequency
        date start_date
        date end_date
        text notes
        datetime created_at
    }

    APPOINTMENTS {
        string appointment_id PK "UUID"
        string user_id FK
        string doctor_name
        string specialization
        date appointment_date
        string appointment_time
        string location
        text notes
        string status "Upcoming | Completed | Cancelled"
        datetime created_at
    }

    AUDIT_LOGS {
        string log_id PK "UUID"
        string user_id FK "Nullable on delete"
        string event_type
        string result "Success | Failure"
        datetime timestamp
        json metadata_info
    }
```
