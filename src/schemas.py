from typing import Literal, Optional
from pydantic import BaseModel, Field


TargetCountry = Literal["vietnam", "cambodia", "myanmar"]


class CountryInfo(BaseModel):
    country_key: TargetCountry
    country_ko: str
    language_ko: str
    language_code: str


class AgentRequest(BaseModel):
    text: str = Field(description="번역할 한국어 광고/마케팅 기획서 내용")
    target_country: TargetCountry = Field(description="대상 국가")
    output_style: str = Field(
        default="기획서 문체",
        description="번역 결과의 문체"
    )


class RetrievedContext(BaseModel):
    marketing_terms: str = ""
    slang_terms: str = ""
    finance_terms: str = ""
    risk_expressions: str = ""


class AgentResponse(BaseModel):
    result_markdown: str
    target_country: str
    target_language: str
    has_risk_expression: bool = False
    detected_summary: Optional[str] = None