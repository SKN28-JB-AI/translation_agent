from typing import Literal
from pydantic import BaseModel, Field


TranslationTaskType = Literal[
    "simple_translation",
    "document_translation",
]


class AgentRequest(BaseModel):
    text: str = Field(description="번역할 원문 텍스트")
    target_country: str = Field(description="vietnam, cambodia, myanmar")
    output_style: str = Field(default="기획서 문체")
    task_type: TranslationTaskType = Field(
        default="simple_translation",
        description="simple_translation 또는 document_translation",
    )


class AgentResponse(BaseModel):
    result_markdown: str
    retrieved_context: str = ""
    exact_matches: str = ""
    target_country_ko: str
    target_language_ko: str