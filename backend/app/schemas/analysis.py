from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(min_length=20)
    job_description: str = Field(min_length=20)

    @field_validator("resume_text", "job_description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Text input cannot be empty.")
        return cleaned


class AnalyzeResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    analysis_summary: str
    strengths: list[str] = Field(min_length=1)
    gaps: list[str] = Field(min_length=1)
    suggestions: list[str] = Field(min_length=1)


class OptimizeRequest(AnalyzeRequest):
    analysis_context: AnalyzeResponse | None = None


class OptimizeResponse(BaseModel):
    optimized_resume_markdown: str
    change_summary: list[str] = Field(min_length=1)


class ResumeParseResponse(BaseModel):
    filename: str
    content_type: str
    resume_text: str
