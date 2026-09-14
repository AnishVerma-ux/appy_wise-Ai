from fastapi import APIRouter

from app.api.routes import (
    analytics,
    applications,
    auth,
    health,
    jobs,
    matching,
    resumes,
)


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(matching.router)
api_router.include_router(applications.router)
api_router.include_router(analytics.router)
api_router.include_router(health.router)