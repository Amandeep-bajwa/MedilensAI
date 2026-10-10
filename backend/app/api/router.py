from fastapi import APIRouter
from app.api.routes import health, auth, users, reports

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users & Management"])
api_router.include_router(reports.router, tags=["Reports Management"])
