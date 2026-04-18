from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.schemas.analysis import AnalyzeResponse, OptimizeResponse


class FakeResumeService:
    async def analyze_resume(self, payload):
        return AnalyzeResponse(
            match_score=78,
            analysis_summary="Strong platform experience with a few role-specific gaps.",
            strengths=["Python and API design", "Fast learning curve", "Relevant backend systems"],
            gaps=["Limited direct domain exposure", "Needs clearer metrics"],
            suggestions=["Add quantified outcomes", "Highlight stakeholder work", "Reorder key skills"],
        )

    async def optimize_resume(self, payload):
        return OptimizeResponse(
            optimized_resume_markdown="# Optimized Resume\n\n## Summary\nUpdated content",
            change_summary=["Reframed summary", "Reordered skills", "Added measurable impact", "Aligned keywords"],
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
    assert "strengths" in body
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
                "analysis_summary": "Strong platform experience with a few role-specific gaps.",
                "strengths": ["Python and API design"],
                "gaps": ["Needs clearer metrics"],
                "suggestions": ["Add quantified outcomes"],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["change_summary"]
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
