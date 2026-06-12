from typing import Literal
from pydantic import BaseModel, Field

TargetCountry = Literal["vietnam", "cambodia", "myanmar"]


class AgentRequest(BaseModel):
    text: str = Field(description="번역할 한국어 광고/마케팅 기획서")
    target_country: TargetCountry = Field(description="대상 국가")
    output_style: str = Field(default="기획서 문체", description="번역 문체")


class AgentResponse(BaseModel):
    result_markdown: str
    retrieved_context: str
    exact_matches: str
    target_country_ko: str
    target_language_ko: str