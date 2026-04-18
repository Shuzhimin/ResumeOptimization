import json

from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.prompts.resume import ANALYZE_SYSTEM_PROMPT, OPTIMIZE_SYSTEM_PROMPT
from backend.app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    OptimizeRequest,
    OptimizeResponse,
)
from backend.app.services.llm_client import DeepSeekClient


class ResumeAgentService:
    def __init__(self, settings: Settings):
        self.client = DeepSeekClient(settings)

    async def analyze_resume(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        prompt = self._build_analysis_prompt(payload.resume_text, payload.job_description)
        data = await self.client.chat_json(ANALYZE_SYSTEM_PROMPT, prompt)
        try:
            return AnalyzeResponse.model_validate(data)
        except ValidationError as exc:
            raise RuntimeError(f"Invalid analysis payload returned by model: {exc}") from exc

    async def optimize_resume(self, payload: OptimizeRequest) -> OptimizeResponse:
        prompt = self._build_optimization_prompt(payload)
        data = await self.client.chat_json(OPTIMIZE_SYSTEM_PROMPT, prompt)
        try:
            return OptimizeResponse.model_validate(data)
        except ValidationError as exc:
            raise RuntimeError(f"Invalid optimization payload returned by model: {exc}") from exc

    @staticmethod
    def _build_analysis_prompt(resume_text: str, job_description: str) -> str:
        return (
            "请基于以下信息分析简历与岗位描述的匹配情况。\n"
            "请注意：返回 JSON 字段名保持英文，但字段内容必须全部使用简体中文。\n\n"
            f"简历内容：\n{resume_text}\n\n"
            f"岗位描述：\n{job_description}\n"
        )

    @staticmethod
    def _build_optimization_prompt(payload: OptimizeRequest) -> str:
        analysis_context = (
            json.dumps(payload.analysis_context.model_dump(), ensure_ascii=False, indent=2)
            if payload.analysis_context
            else "未提供历史分析结果。"
        )
        return (
            "请在不虚构事实的前提下，根据岗位描述优化这份简历。\n"
            "请注意：返回 JSON 字段名保持英文，但字段内容必须全部使用简体中文。\n\n"
            f"原始简历：\n{payload.resume_text}\n\n"
            f"岗位描述：\n{payload.job_description}\n\n"
            f"分析上下文：\n{analysis_context}\n"
        )
