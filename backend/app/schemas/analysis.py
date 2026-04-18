from pydantic import BaseModel, Field, field_validator


SECTION_ORDER = [
    "header",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "other",
]


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


class DetectedSection(BaseModel):
    section_type: str
    section_title: str
    raw_content: str
    order: int = Field(ge=0)


class SectionAnalysisItem(BaseModel):
    section_type: str
    section_title: str
    needs_optimization: bool
    priority: str
    reason: str
    optimization_focus: list[str] = Field(default_factory=list)
    missing_but_recommended: bool = False


class AnalyzeResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    analysis_summary: str
    strengths: list[str] = Field(min_length=1)
    gaps: list[str] = Field(min_length=1)
    suggestions: list[str] = Field(min_length=1)
    detected_sections: list[DetectedSection] = Field(default_factory=list)
    section_analysis: list[SectionAnalysisItem] = Field(default_factory=list)


class OptimizeRequest(AnalyzeRequest):
    analysis_context: AnalyzeResponse | None = None


class OptimizedSection(BaseModel):
    section_type: str
    section_title: str
    original_content: str
    optimized_content: str
    updated: bool
    change_summary: list[str] = Field(default_factory=list)


class OptimizeResponse(BaseModel):
    optimized_resume_markdown: str
    change_summary: list[str] = Field(min_length=1)
    detected_sections: list[DetectedSection] = Field(default_factory=list)
    optimized_sections: list[OptimizedSection] = Field(default_factory=list)
    assembly_order: list[str] = Field(default_factory=list)


class ResumeParseResponse(BaseModel):
    filename: str
    content_type: str
    resume_text: str
