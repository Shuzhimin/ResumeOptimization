from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    OptimizeRequest,
    OptimizeResponse,
)
from backend.app.services.resume_service import ResumeAgentService

router = APIRouter()


def get_resume_service(settings: Settings = Depends(get_settings)) -> ResumeAgentService:
    return ResumeAgentService(settings)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_resume(
    payload: AnalyzeRequest,
    service: ResumeAgentService = Depends(get_resume_service),
) -> AnalyzeResponse:
    try:
        return await service.analyze_resume(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(
    payload: OptimizeRequest,
    service: ResumeAgentService = Depends(get_resume_service),
) -> OptimizeResponse:
    try:
        return await service.optimize_resume(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
