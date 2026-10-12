from fastapi import APIRouter
from app.api.routes import (
    health,
    auth,
    users,
    reports,
    ocr,
    ai,
    rag,
    symptoms,
    medications,
    appointments,
    dashboard,
    notifications
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users & Management"])
api_router.include_router(reports.router, tags=["Reports Management"])
api_router.include_router(ocr.router, tags=["OCR & Document Processing"])
api_router.include_router(ai.router, tags=["AI Report Explanation & Clinical Insights"])
api_router.include_router(rag.router, tags=["Report-Grounded RAG Q&A Engine"])
api_router.include_router(symptoms.router, tags=["Symptom Assistant & Clinical Triage"])
api_router.include_router(medications.router, tags=["Medications Management"])
api_router.include_router(appointments.router, tags=["Appointments Management"])
api_router.include_router(dashboard.router, tags=["Dashboard & Clinical Analytics"])
api_router.include_router(notifications.router, tags=["Notifications & Clinical Reminders"])



