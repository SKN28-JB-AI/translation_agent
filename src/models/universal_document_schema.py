from typing import Literal
from pydantic import BaseModel, Field


BlockType = Literal[
    "title",
    "subtitle",
    "header_text",
    "meta_table",
    "summary_table",
    "section",
    "paragraph",
    "bullet_list",
    "table",
    "note",
    "divider",
]


LayoutStyle = Literal[
    "compact_form_report",
    "general_report",
    "table_heavy_report",
    "slide_summary",
]


IssueCategory = Literal[
    "오역",
    "누락",
    "추가",
    "문체",
    "용어",
    "형식",
    "위험표현",
    "기타",
]


class UniversalBlock(BaseModel):
    type: BlockType = Field(description="문서 블록 유형")
    title: str = Field(default="", description="블록 제목")
    text: str = Field(default="", description="문단 또는 단일 텍스트")
    rows: list[list[str]] = Field(default_factory=list, description="표 데이터")
    items: list[str] = Field(default_factory=list, description="목록 항목")
    level: int = Field(default=1, description="제목/섹션 레벨")
    order: int = Field(default=0, description="문서 내 순서")


class UniversalDocument(BaseModel):
    document_type: str = Field(description="문서 유형")
    layout_style: LayoutStyle = Field(description="문서 레이아웃 스타일")
    title: str = Field(description="문서 제목")
    summary: str = Field(default="", description="문서 전체 요약")
    blocks: list[UniversalBlock] = Field(default_factory=list)


class TranslatedUniversalDocument(BaseModel):
    target_country: str = Field(description="대상 국가")
    target_language: str = Field(description="대상 언어")
    document_type: str = Field(description="문서 유형")
    layout_style: LayoutStyle = Field(description="문서 레이아웃 스타일")
    title: str = Field(description="번역된 문서 제목")
    summary: str = Field(default="", description="번역된 문서 요약")
    blocks: list[UniversalBlock] = Field(default_factory=list)


class TranslationReviewIssue(BaseModel):
    category: IssueCategory = Field(description="문제 유형")
    original_part: str = Field(default="", description="원문에서 문제가 된 부분")
    translated_part: str = Field(default="", description="번역문에서 문제가 된 부분")
    reason: str = Field(description="문제라고 판단한 이유")
    suggestion: str = Field(default="", description="수정 제안")


class TranslationReviewResult(BaseModel):
    target_country: str = Field(description="대상 국가")
    target_language: str = Field(description="대상 언어")
    overall_score: int = Field(description="전체 번역 품질 점수. 1~100")
    verdict: str = Field(description="전체 판단. 예: 양호, 일부 수정 필요, 재번역 권장")
    back_translation_summary_ko: str = Field(description="번역문을 한국어로 되돌려 요약한 내용")
    back_translated_document_ko: str = Field(description="번역문 전체를 한국어로 되돌려 확인한 내용")
    good_points: list[str] = Field(default_factory=list, description="잘 번역된 점")
    issues: list[TranslationReviewIssue] = Field(default_factory=list, description="검수 중 발견된 문제")
    missing_or_added_content: str = Field(default="", description="누락되거나 추가된 내용 여부")
    terminology_notes: str = Field(default="", description="용어 번역 관련 검토 의견")
    format_notes: str = Field(default="", description="표, 섹션, 문서 구조 유지 여부")
    final_comment: str = Field(default="", description="최종 검수 의견")