from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader

from backend.app.core.config import Settings
from backend.app.schemas.analysis import ResumeParseResponse


class FileParserService:
    allowed_types = {
        "text/plain": ".txt",
        "application/pdf": ".pdf",
    }

    def __init__(self, settings: Settings):
        self.settings = settings

    async def parse_resume(self, file: UploadFile) -> ResumeParseResponse:
        if not file.filename:
            raise ValueError("Missing filename.")

        extension = self._get_extension(file.filename)
        if extension not in self.allowed_types.values():
            raise ValueError("Unsupported file type. Only TXT and PDF are allowed.")

        contents = await file.read()
        if not contents:
            raise ValueError("Uploaded file is empty.")

        max_size = self.settings.max_upload_size_mb * 1024 * 1024
        if len(contents) > max_size:
            raise ValueError(f"File too large. Max size is {self.settings.max_upload_size_mb}MB.")

        if extension == ".txt":
            resume_text = self._parse_txt(contents)
            content_type = file.content_type or "text/plain"
        else:
            resume_text = self._parse_pdf(contents)
            content_type = file.content_type or "application/pdf"

        if len(resume_text.strip()) < 20:
            raise ValueError("Could not extract enough text from the uploaded resume.")

        return ResumeParseResponse(
            filename=file.filename,
            content_type=content_type,
            resume_text=resume_text.strip(),
        )

    @staticmethod
    def _get_extension(filename: str) -> str:
        lower_name = filename.lower()
        if lower_name.endswith(".txt"):
            return ".txt"
        if lower_name.endswith(".pdf"):
            return ".pdf"
        return ""

    @staticmethod
    def _parse_txt(contents: bytes) -> str:
        try:
            return contents.decode("utf-8")
        except UnicodeDecodeError:
            return contents.decode("utf-8", errors="ignore")

    @staticmethod
    def _parse_pdf(contents: bytes) -> str:
        reader = PdfReader(BytesIO(contents))
        text_chunks = [page.extract_text() or "" for page in reader.pages]
        merged = "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip())
        if not merged:
            raise ValueError("The PDF appears to contain no extractable text.")
        return merged
