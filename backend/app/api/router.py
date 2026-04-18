from fastapi import APIRouter

from backend.app.api.routes import analysis, files

api_router = APIRouter()
api_router.include_router(analysis.router, tags=["analysis"])
api_router.include_router(files.router, tags=["files"])
