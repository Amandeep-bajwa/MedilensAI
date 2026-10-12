from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.core.errors import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.api.router import api_router
from app.core.rate_limit import limiter, rate_limit_custom_handler
from app.core.middleware import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded
import app.models  # ensure models are loaded

# Ensure database tables exist across test clients and runtime
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure upload dir and database tables exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown logic (if any)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for MediLens AI - AI-Powered Healthcare Symptom & Medical Report Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Register slowapi rate limiter state
app.state.limiter = limiter

# Security Headers & CORS Middleware (SEC-INP, SEC-PRIV)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers (SRS Section 16 compliant)
app.add_exception_handler(RateLimitExceeded, rate_limit_custom_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to MediLens AI API",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
