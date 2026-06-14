from typing import Literal
from pydantic import BaseModel, Field

from models.universal_document_schema import TranslatedUniversalDocument


TranslationTaskType = Literal[
    "simple_translation",
    "document_translation",
]


class TextTranslateRequest(BaseModel):
    text: str = Field(description="번역할 한국어 텍스트")
    target_country: str = Field(description="vietnam, cambodia, myanmar")
    output_style: str = Field(default="기획서 문체")
    task_type: TranslationTaskType = Field(
        default="simple_translation",
        description="simple_translation 또는 document_translation",
    )


class TextTranslateResponse(BaseModel):
    target_country_ko: str
    target_language_ko: str
    result_markdown: str


class ReportReviewRequest(BaseModel):
    original_text: str
    target_country: str
    translated_document: TranslatedUniversalDocument


class PdfGenerateRequest(BaseModel):
    original_filename: str = "translated_report.pdf"
    translated_document: TranslatedUniversalDocument