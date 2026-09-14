from fastapi import APIRouter

from app.api.routes import auth, health, jobs, resumes


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(health.router)