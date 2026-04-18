from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.schemas.analysis import (
    AnalyzeResponse,
    DetectedSection,
    OptimizeResponse,
    OptimizedSection,
    SectionAnalysisItem,
)


class FakeResumeService:
    async def analyze_resume(self, payload):
        return AnalyzeResponse(
            match_score=78,
            analysis_summary="候选人与岗位基础能力较匹配，但部分 section 仍需针对性优化。",
            strengths=["具备 Python 后端开发经验", "有 API 设计与交付能力", "工程协作基础较好"],
            gaps=["成果量化不足", "岗位关键词覆盖不够", "职业概述不够聚焦"],
            suggestions=["补充量化成果", "强化目标岗位关键词", "调整 section 顺序"],
            detected_sections=[
                DetectedSection(section_type="header", section_title="基本信息", raw_content="张三\n邮箱: demo@example.com", order=0),
                DetectedSection(section_type="summary", section_title="职业概述", raw_content="后端工程师，负责 API 开发。", order=1),
            ],
            section_analysis=[
                SectionAnalysisItem(
                    section_type="header",
                    section_title="基本信息",
                    needs_optimization=False,
                    priority="low",
                    reason="基本信息完整，可保留。",
                    optimization_focus=[],
                    missing_but_recommended=False,
                ),
                SectionAnalysisItem(
                    section_type="summary",
                    section_title="职业概述",
                    needs_optimization=True,
                    priority="high",
                    reason="概述未突出目标岗位相关性。",
                    optimization_focus=["突出 Python 后端经验", "强调接口设计与交付成果"],
                    missing_but_recommended=False,
                ),
            ],
        )

    async def optimize_resume(self, payload):
        return OptimizeResponse(
            optimized_resume_markdown="# 张三\n\n## 职业概述\n聚焦 Python 后端开发与 API 交付。",
            change_summary=["重写职业概述", "强化岗位关键词", "保留基础信息"],
            detected_sections=[
                DetectedSection(section_type="header", section_title="基本信息", raw_content="张三\n邮箱: demo@example.com", order=0),
                DetectedSection(section_type="summary", section_title="职业概述", raw_content="后端工程师，负责 API 开发。", order=1),
            ],
            optimized_sections=[
                OptimizedSection(
                    section_type="header",
                    section_title="基本信息",
                    original_content="张三\n邮箱: demo@example.com",
                    optimized_content="张三\n邮箱: demo@example.com",
                    updated=False,
                    change_summary=["保留原有基础信息。"],
                ),
                OptimizedSection(
                    section_type="summary",
                    section_title="职业概述",
                    original_content="后端工程师，负责 API 开发。",
                    optimized_content="聚焦 Python 后端开发与 API 交付。",
                    updated=True,
                    change_summary=["重写职业概述", "突出岗位关键词"],
                ),
            ],
            assembly_order=["header", "summary"],
        )


client = TestClient(app)


def override_resume_service():
    return FakeResumeService()


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_endpoint():
    from backend.app.api.routes.analysis import get_resume_service

    app.dependency_overrides[get_resume_service] = override_resume_service
    response = client.post(
        "/api/v1/analyze",
        json={
            "resume_text": "Experienced backend engineer with Python, APIs, and platform delivery.",
            "job_description": "Seeking a backend engineer with Python, APIs, teamwork, and metrics.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["match_score"] == 78
    assert len(body["detected_sections"]) == 2
    assert body["section_analysis"][1]["needs_optimization"] is True
    app.dependency_overrides.clear()


def test_optimize_endpoint():
    from backend.app.api.routes.analysis import get_resume_service

    app.dependency_overrides[get_resume_service] = override_resume_service
    response = client.post(
        "/api/v1/optimize",
        json={
            "resume_text": "Experienced backend engineer with Python, APIs, and platform delivery.",
            "job_description": "Seeking a backend engineer with Python, APIs, teamwork, and metrics.",
            "analysis_context": {
                "match_score": 78,
                "analysis_summary": "候选人与岗位基础能力较匹配，但部分 section 仍需针对性优化。",
                "strengths": ["具备 Python 后端开发经验"],
                "gaps": ["职业概述不够聚焦"],
                "suggestions": ["强化目标岗位关键词"],
                "detected_sections": [
                    {"section_type": "header", "section_title": "基本信息", "raw_content": "张三\n邮箱: demo@example.com", "order": 0},
                    {"section_type": "summary", "section_title": "职业概述", "raw_content": "后端工程师，负责 API 开发。", "order": 1},
                ],
                "section_analysis": [
                    {
                        "section_type": "header",
                        "section_title": "基本信息",
                        "needs_optimization": False,
                        "priority": "low",
                        "reason": "基本信息完整，可保留。",
                        "optimization_focus": [],
                        "missing_but_recommended": False,
                    },
                    {
                        "section_type": "summary",
                        "section_title": "职业概述",
                        "needs_optimization": True,
                        "priority": "high",
                        "reason": "概述未突出目标岗位相关性。",
                        "optimization_focus": ["突出 Python 后端经验"],
                        "missing_but_recommended": False,
                    },
                ],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["optimized_sections"][1]["updated"] is True
    assert body["assembly_order"] == ["header", "summary"]
    app.dependency_overrides.clear()


def test_parse_txt_resume():
    response = client.post(
        "/api/v1/parse-resume",
        files={"file": ("resume.txt", b"Resume summary\nPython engineer with delivery ownership.", "text/plain")},
    )
    assert response.status_code == 200
    assert "Python engineer" in response.json()["resume_text"]


def test_parse_invalid_extension():
    response = client.post(
        "/api/v1/parse-resume",
        files={"file": ("resume.docx", b"binary", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 400


def test_settings_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.deepseek_base_url == "https://api.deepseek.com"
