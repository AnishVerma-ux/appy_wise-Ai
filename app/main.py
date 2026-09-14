from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="AI-powered job application tracking backend.",
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
    }

