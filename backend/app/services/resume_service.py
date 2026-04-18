import json

from pydantic import BaseModel, ValidationError

from backend.app.core.config import Settings
from backend.app.prompts.resume import (
    ANALYZE_SYSTEM_PROMPT,
    SECTION_ANALYSIS_PROMPT,
    SECTION_EXTRACTION_PROMPT,
    SECTION_OPTIMIZATION_PROMPT,
)
from backend.app.schemas.analysis import (
    SECTION_ORDER,
    AnalyzeRequest,
    AnalyzeResponse,
    DetectedSection,
    OptimizeRequest,
    OptimizeResponse,
    OptimizedSection,
    SectionAnalysisItem,
)
from backend.app.services.llm_client import DeepSeekClient


class SectionExtractionResult(BaseModel):
    sections: list[DetectedSection]


class SectionAnalysisResult(BaseModel):
    section_analysis: list[SectionAnalysisItem]


class SectionOptimizationResult(BaseModel):
    section_type: str
    section_title: str
    optimized_content: str
    change_summary: list[str]


class ResumeAgentService:
    def __init__(self, settings: Settings):
        self.client = DeepSeekClient(settings)

    async def analyze_resume(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        summary_prompt = self._build_analysis_prompt(payload.resume_text, payload.job_description)
        summary_data = await self.client.chat_json(ANALYZE_SYSTEM_PROMPT, summary_prompt)
        try:
            summary = AnalyzeResponse.model_validate(
                {
                    "match_score": summary_data["match_score"],
                    "analysis_summary": summary_data["analysis_summary"],
                    "strengths": summary_data["strengths"],
                    "gaps": summary_data["gaps"],
                    "suggestions": summary_data["suggestions"],
                }
            )
        except (ValidationError, KeyError) as exc:
            raise RuntimeError(f"Invalid analysis payload returned by model: {exc}") from exc

        detected_sections = await self._extract_sections(payload.resume_text)
        section_analysis = await self._analyze_sections(
            payload.resume_text,
            payload.job_description,
            detected_sections,
        )

        return AnalyzeResponse(
            match_score=summary.match_score,
            analysis_summary=summary.analysis_summary,
            strengths=summary.strengths,
            gaps=summary.gaps,
            suggestions=summary.suggestions,
            detected_sections=detected_sections,
            section_analysis=section_analysis,
        )

    async def optimize_resume(self, payload: OptimizeRequest) -> OptimizeResponse:
        detected_sections = (
            payload.analysis_context.detected_sections if payload.analysis_context and payload.analysis_context.detected_sections else None
        )
        if not detected_sections:
            detected_sections = await self._extract_sections(payload.resume_text)

        section_analysis = (
            payload.analysis_context.section_analysis if payload.analysis_context and payload.analysis_context.section_analysis else None
        )
        if not section_analysis:
            section_analysis = await self._analyze_sections(
                payload.resume_text,
                payload.job_description,
                detected_sections,
            )

        optimized_sections = await self._optimize_sections(
            payload.job_description,
            detected_sections,
            section_analysis,
        )
        optimized_resume_markdown = self._assemble_resume(optimized_sections)
        aggregated_change_summary = self._aggregate_change_summary(optimized_sections)

        return OptimizeResponse(
            optimized_resume_markdown=optimized_resume_markdown,
            change_summary=aggregated_change_summary,
            detected_sections=detected_sections,
            optimized_sections=optimized_sections,
            assembly_order=[section.section_type for section in optimized_sections],
        )

    async def _extract_sections(self, resume_text: str) -> list[DetectedSection]:
        try:
            data = await self.client.chat_json(
                SECTION_EXTRACTION_PROMPT,
                self._build_section_extraction_prompt(resume_text),
            )
            result = SectionExtractionResult.model_validate(data)
            normalized_sections = sorted(result.sections, key=lambda item: item.order)
            if normalized_sections:
                return normalized_sections
        except (RuntimeError, ValidationError):
            pass

        return self._fallback_extract_sections(resume_text)

    async def _analyze_sections(
        self,
        resume_text: str,
        job_description: str,
        detected_sections: list[DetectedSection],
    ) -> list[SectionAnalysisItem]:
        try:
            data = await self.client.chat_json(
                SECTION_ANALYSIS_PROMPT,
                self._build_section_analysis_prompt(resume_text, job_description, detected_sections),
            )
            result = SectionAnalysisResult.model_validate(data)
        except (RuntimeError, ValidationError):
            return self._fallback_section_analysis(job_description, detected_sections)

        analysis_by_key = {(item.section_type, item.section_title): item for item in result.section_analysis}
        merged: list[SectionAnalysisItem] = []

        for section in detected_sections:
            merged.append(
                analysis_by_key.get(
                    (section.section_type, section.section_title),
                    SectionAnalysisItem(
                        section_type=section.section_type,
                        section_title=section.section_title,
                        needs_optimization=False,
                        priority="low",
                        reason="该部分结构完整，可先保留原文。",
                        optimization_focus=[],
                        missing_but_recommended=False,
                    ),
                )
            )

        for item in result.section_analysis:
            key = (item.section_type, item.section_title)
            if key not in {(section.section_type, section.section_title) for section in detected_sections} and item.missing_but_recommended:
                merged.append(item)

        return merged

    async def _optimize_sections(
        self,
        job_description: str,
        detected_sections: list[DetectedSection],
        section_analysis: list[SectionAnalysisItem],
    ) -> list[OptimizedSection]:
        section_lookup = {(section.section_type, section.section_title): section for section in detected_sections}
        optimized_sections: list[OptimizedSection] = []

        for analysis_item in section_analysis:
            source_section = section_lookup.get((analysis_item.section_type, analysis_item.section_title))
            original_content = source_section.raw_content if source_section else ""

            if not analysis_item.needs_optimization and not analysis_item.missing_but_recommended:
                optimized_sections.append(
                    OptimizedSection(
                        section_type=analysis_item.section_type,
                        section_title=analysis_item.section_title,
                        original_content=original_content,
                        optimized_content=original_content,
                        updated=False,
                        change_summary=["该部分与目标岗位匹配度较高，保留原有信息结构。"],
                    )
                )
                continue

            data = await self.client.chat_json(
                SECTION_OPTIMIZATION_PROMPT,
                self._build_section_optimization_prompt(job_description, analysis_item, original_content),
            )
            try:
                result = SectionOptimizationResult.model_validate(data)
            except ValidationError as exc:
                raise RuntimeError(f"Invalid section optimization payload returned by model: {exc}") from exc

            optimized_sections.append(
                OptimizedSection(
                    section_type=analysis_item.section_type,
                    section_title=result.section_title or analysis_item.section_title,
                    original_content=original_content,
                    optimized_content=result.optimized_content.strip(),
                    updated=True,
                    change_summary=result.change_summary,
                )
            )

        ordered_sections = sorted(
            optimized_sections,
            key=lambda item: (
                SECTION_ORDER.index(item.section_type) if item.section_type in SECTION_ORDER else len(SECTION_ORDER),
                item.section_title,
            ),
        )
        return ordered_sections

    @staticmethod
    def _aggregate_change_summary(optimized_sections: list[OptimizedSection]) -> list[str]:
        items: list[str] = []
        for section in optimized_sections:
            if section.updated:
                items.extend(section.change_summary)

        deduplicated: list[str] = []
        for item in items:
            if item not in deduplicated:
                deduplicated.append(item)

        if deduplicated:
            return deduplicated[:8]

        return ["简历整体结构已整理完成，当前版本保留了原有信息表达。"]

    @staticmethod
    def _assemble_resume(optimized_sections: list[OptimizedSection]) -> str:
        blocks: list[str] = []
        title_mapping = {
            "header": "",
            "summary": "## 职业概述",
            "skills": "## 核心技能",
            "experience": "## 工作经历",
            "projects": "## 项目经历",
            "education": "## 教育背景",
            "certifications": "## 证书与补充信息",
            "other": "## 其他信息",
        }

        for section in optimized_sections:
            content = section.optimized_content.strip()
            if not content:
                continue

            if section.section_type == "header":
                blocks.append(content)
                continue

            title = title_mapping.get(section.section_type) or f"## {section.section_title}"
            if content.startswith("#"):
                blocks.append(content)
            else:
                blocks.append(f"{title}\n{content}")

        return "\n\n".join(blocks).strip()

    @staticmethod
    def _build_analysis_prompt(resume_text: str, job_description: str) -> str:
        return (
            "请基于以下信息分析简历与岗位描述的匹配情况。\n"
            "请注意：返回 JSON 字段名保持英文，但字段内容必须全部使用简体中文。\n\n"
            f"简历内容：\n{resume_text}\n\n"
            f"岗位描述：\n{job_description}\n"
        )

    @staticmethod
    def _build_section_extraction_prompt(resume_text: str) -> str:
        return (
            "请先识别这份简历包含哪些 section，并将内容尽量完整地映射到标准类型中。\n"
            "如果标题不标准，请根据内容语义归类。\n\n"
            f"简历内容：\n{resume_text}\n"
        )

    @staticmethod
    def _build_section_analysis_prompt(
        resume_text: str,
        job_description: str,
        detected_sections: list[DetectedSection],
    ) -> str:
        sections_json = json.dumps([section.model_dump() for section in detected_sections], ensure_ascii=False, indent=2)
        return (
            "请根据目标岗位分析每个简历 section 是否需要优化。\n"
            "如果某个重要 section 缺失，也请给出 missing_but_recommended=true 的判断。\n\n"
            f"原始简历：\n{resume_text}\n\n"
            f"岗位描述：\n{job_description}\n\n"
            f"已识别的简历 sections：\n{sections_json}\n"
        )

    @staticmethod
    def _build_section_optimization_prompt(
        job_description: str,
        analysis_item: SectionAnalysisItem,
        original_content: str,
    ) -> str:
        analysis_json = json.dumps(analysis_item.model_dump(), ensure_ascii=False, indent=2)
        content = original_content if original_content else "该 section 在原简历中缺失。"
        return (
            "请只优化当前这个简历 section，不要输出完整简历。\n"
            "请注意：输出必须是最终可用中文 section 内容。\n\n"
            f"岗位描述：\n{job_description}\n\n"
            f"当前 section 诊断：\n{analysis_json}\n\n"
            f"当前 section 原文：\n{content}\n"
        )

    @staticmethod
    def _fallback_extract_sections(resume_text: str) -> list[DetectedSection]:
        lines = [line.strip() for line in resume_text.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return [DetectedSection(section_type="other", section_title="简历内容", raw_content=resume_text.strip(), order=0)]

        sections: list[DetectedSection] = []
        current_title = "基本信息"
        current_type = "header"
        current_content: list[str] = []

        def flush_section(order: int):
            nonlocal current_content
            if not current_content:
                return None
            section = DetectedSection(
                section_type=current_type,
                section_title=current_title,
                raw_content="\n".join(current_content).strip(),
                order=order,
            )
            current_content = []
            return section

        order = 0
        heading_map = {
            "职业概述": "summary",
            "个人简介": "summary",
            "核心技能": "skills",
            "专业技能": "skills",
            "工作经历": "experience",
            "项目经历": "projects",
            "教育背景": "education",
            "教育经历": "education",
            "证书": "certifications",
            "证书与荣誉": "certifications",
        }

        for line in lines:
            mapped_type = heading_map.get(line)
            if mapped_type:
                section = flush_section(order)
                if section:
                    sections.append(section)
                    order += 1
                current_title = line
                current_type = mapped_type
                continue
            current_content.append(line)

        section = flush_section(order)
        if section:
            sections.append(section)

        if not sections:
            sections.append(DetectedSection(section_type="other", section_title="简历内容", raw_content=resume_text.strip(), order=0))

        return sections

    @staticmethod
    def _fallback_section_analysis(
        job_description: str,
        detected_sections: list[DetectedSection],
    ) -> list[SectionAnalysisItem]:
        jd_lower = job_description.lower()
        section_items: list[SectionAnalysisItem] = []
        existing_types = {section.section_type for section in detected_sections}

        for section in detected_sections:
            content_lower = section.raw_content.lower()
            needs_optimization = section.section_type in {"summary", "skills", "experience", "projects"}
            if any(keyword in jd_lower and keyword not in content_lower for keyword in ["python", "api", "java", "sql", "golang"]):
                needs_optimization = True

            section_items.append(
                SectionAnalysisItem(
                    section_type=section.section_type,
                    section_title=section.section_title,
                    needs_optimization=needs_optimization,
                    priority="high" if needs_optimization else "low",
                    reason="该部分与目标岗位的关键词或表达方式仍有优化空间。" if needs_optimization else "该部分信息完整，可先保留。",
                    optimization_focus=["强化与目标岗位相关的关键词", "保留事实并优化表达"] if needs_optimization else [],
                    missing_but_recommended=False,
                )
            )

        for missing_type, title in [("summary", "职业概述"), ("skills", "核心技能")]:
            if missing_type not in existing_types:
                section_items.append(
                    SectionAnalysisItem(
                        section_type=missing_type,
                        section_title=title,
                        needs_optimization=True,
                        priority="medium",
                        reason="该部分在目标岗位场景中通常应明确呈现，建议补充。",
                        optimization_focus=["基于现有简历事实补出该部分结构"],
                        missing_but_recommended=True,
                    )
                )

        return section_items
