from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.analysis import ResumeParseResponse
from backend.app.services.file_parser import FileParserService

router = APIRouter()


def get_file_parser(settings: Settings = Depends(get_settings)) -> FileParserService:
    return FileParserService(settings)


@router.post("/parse-resume", response_model=ResumeParseResponse)
async def parse_resume(
    file: UploadFile = File(...),
    parser: FileParserService = Depends(get_file_parser),
) -> ResumeParseResponse:
    try:
        return await parser.parse_resume(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
