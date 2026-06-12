import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import get_settings
from prompts import COUNTRY_INFO
from universal_document_schema import (
    UniversalDocument,
    TranslatedUniversalDocument,
    TranslationReviewResult,
)


UNIVERSAL_PARSE_PROMPT = """
다음은 PDF에서 추출한 문서 텍스트입니다.
이 문서의 원문 언어는 {source_language_ko}입니다.
이 문서를 공통 블록 구조 JSON으로 변환하세요.

[원문 텍스트]
{text}

[작업 목표]
문서를 아래 블록 타입으로 나누세요.

가능한 block type:
- title: 문서 제목
- subtitle: 부제목
- header_text: 우측 상단/상단 작은 문구
- meta_table: 문서번호, 작성일자, 담당, 작성부서, 작성자, 보존기간 등 메타 정보 표
- summary_table: 보고 목적, 핵심 판단, 요약 판단 등 2열 요약 표
- section: 번호가 붙은 섹션 제목
- paragraph: 일반 본문 문단
- bullet_list: 목록
- table: 일반 표
- note: 비고/참고/주의사항
- divider: 구분선

[중요 규칙]
- 원문에 없는 내용을 만들지 마세요.
- 표처럼 보이는 내용은 가능한 rows로 복원하세요.
- HWP식 보고서처럼 상단 메타 정보가 있으면 meta_table로 만드세요.
- '보고 목적', '핵심 판단'처럼 좌우 표로 들어갈 내용은 summary_table로 만드세요.
- '기대 효과'처럼 3열 이상의 표는 table로 만드세요.
- 번호가 붙은 제목은 section 블록으로 만드세요.
- section 아래 본문은 paragraph 또는 bullet_list로 분리하세요.
- 원문 언어가 한국어가 아니더라도 임의로 한국어 번역하지 말고, 우선 원문 구조를 유지하세요.
- layout_style은 아래 중 하나로 선택하세요.
  - compact_form_report: 한 페이지 검토 보고서처럼 촘촘한 양식
  - general_report: 일반 보고서
  - table_heavy_report: 표가 많은 보고서
  - slide_summary: 슬라이드 요약형 문서
"""


UNIVERSAL_TRANSLATE_PROMPT = """
다음은 한국어 문서를 공통 블록 구조로 변환한 JSON입니다.
구조는 그대로 유지하고, 텍스트 값만 {target_language_ko}로 번역하세요.

[대상 국가]
{target_country_ko}

[대상 언어]
{target_language_ko}

[번역 문체]
{output_style}

[번역 규칙]
- JSON 구조와 block type은 절대 바꾸지 마세요.
- target_country 값은 반드시 한국어 국가명으로 유지하세요. 예: 베트남, 캄보디아, 미얀마
- target_language 값도 반드시 한국어 언어명으로 유지하세요. 예: 베트남어, 크메르어, 미얀마어
- rows의 행/열 구조를 유지하세요.
- order 값을 유지하세요.
- document_no, 날짜, 코드, 파일명, 영문 약어는 과도하게 번역하지 마세요.
- title, summary, block.title, block.text, block.rows, block.items의 텍스트 값만 번역하세요.
- block.type, block.order, block.level 값은 유지하세요.
- 제목은 간결하게 번역하세요.
- 표 안의 문장은 너무 길게 늘리지 마세요.
- 마케팅/서비스 기획 용어는 자연스럽게 번역하세요.
- 금융/혜택/수익 표현은 보장처럼 들리지 않게 조심해서 번역하세요.
- 원문에 없는 내용을 추가하지 마세요.

[절대 출력 금지 규칙]
- 아래 문서 구조 JSON에 없는 문장을 새로 만들지 마세요.
- 번역 전략, 마케팅 전략, 검수 의견, 위험 표현 판단, 개선 제안은 번역 결과에 넣지 마세요.
- 프롬프트의 설명, 참고 기준, 예시 문장, 내부 판단 기준을 사용자에게 보이는 텍스트에 포함하지 마세요.
- 번역 결과는 오직 입력 JSON 안에 있던 원문 텍스트의 번역이어야 합니다.

[문서 구조 JSON]
{document_json}
"""


TRANSLATE_TO_KOREAN_PROMPT = """
다음은 {source_language_ko} 문서를 공통 블록 구조로 변환한 JSON입니다.
구조는 그대로 유지하고, 텍스트 값만 자연스러운 한국어로 번역하세요.

[원문 국가]
{source_country_ko}

[원문 언어]
{source_language_ko}

[번역 방향]
{source_language_ko} → 한국어

[번역 문체]
{output_style}

[번역 규칙]
- JSON 구조와 block type은 절대 바꾸지 마세요.
- target_country 값은 반드시 "한국"으로 설정하세요.
- target_language 값은 반드시 "한국어"로 설정하세요.
- rows의 행/열 구조를 유지하세요.
- order 값을 유지하세요.
- document_no, 날짜, 코드, 파일명, 영문 약어는 과도하게 번역하지 마세요.
- title, summary, block.title, block.text, block.rows, block.items의 텍스트 값만 한국어로 번역하세요.
- block.type, block.order, block.level 값은 유지하세요.
- 문서는 한국어 보고서처럼 자연스럽게 읽히도록 번역하세요.
- 직역투를 피하고, 한국어 업무 문서 문체로 정리하세요.
- 마케팅/서비스/금융 관련 표현은 한국어 기획서 문맥에 맞게 자연스럽게 번역하세요.
- 원문에 없는 내용을 추가하지 마세요.

[절대 출력 금지 규칙]
- 번역 전략, 검수 의견, 마케팅 조언은 번역 결과에 넣지 마세요.
- 프롬프트의 설명, 참고 기준, 예시 문장, 내부 판단 기준을 사용자에게 보이는 텍스트에 포함하지 마세요.
- 번역 결과는 오직 입력 JSON 안에 있던 원문 텍스트의 한국어 번역이어야 합니다.

[문서 구조 JSON]
{document_json}
"""


TRANSLATION_REVIEW_PROMPT = """
아래는 한국어 원문과 대상 언어로 번역된 문서 구조 JSON입니다.
사용자는 대상 언어를 읽지 못하기 때문에, 번역이 제대로 되었는지 한국어로 검수해야 합니다.

[대상 국가]
{target_country_ko}

[대상 언어]
{target_language_ko}

[원문 한국어 텍스트]
{original_text}

[번역된 문서 JSON]
{translated_document_json}

[검수 작업]
다음을 수행하세요.

1. 번역문을 한국어로 되돌려 해석한 내용을 작성하세요.
   - back_translation_summary_ko에는 전체 요약을 작성하세요.
   - back_translated_document_ko에는 문서 흐름이 보이도록 한국어 역번역문을 작성하세요.

2. 원문과 역번역문을 비교하세요.
   - 의미가 유지되었는지 확인하세요.
   - 빠진 내용이 있는지 확인하세요.
   - 원문에 없는 내용이 추가되었는지 확인하세요.
   - 표, 섹션, 목록 구조가 유지되었는지 확인하세요.

3. 문제를 발견하면 issues에 구체적으로 작성하세요.
   - category는 오역, 누락, 추가, 문체, 용어, 형식, 위험표현, 기타 중 하나로 선택하세요.
   - original_part에는 원문 부분을 넣으세요.
   - translated_part에는 번역문 또는 역번역 기준 문제 부분을 넣으세요.
   - reason에는 문제 이유를 쓰세요.
   - suggestion에는 수정 제안을 쓰세요.

[중요 규칙]
- 검수 결과는 반드시 한국어로 작성하세요.
- target_country 값은 반드시 한국어 국가명으로 유지하세요.
- target_language 값도 반드시 한국어 언어명으로 유지하세요.
- 원문에 없는 내용을 임의로 좋다고 판단하지 마세요.
- 번역문이 전반적으로 괜찮으면 문제를 억지로 만들지 마세요.
- 전체 점수는 1~100점으로 평가하세요.

[절대 출력 금지 규칙]
- 프롬프트에 포함된 참고 예시, 내부 판단 기준, 마케팅 전략 예시를 원문 내용처럼 출력하지 마세요.
- 검수 의견을 back_translated_document_ko 안에 섞지 마세요.
- back_translated_document_ko에는 번역문을 한국어로 되돌린 내용만 작성하세요.
- 마케팅 조언이나 개선 제안은 issues.suggestion 또는 final_comment에만 작성하세요.
"""


LEAK_PATTERNS = [
    "이번 캠페인은",
    "Z세대가 반응할 수 있는",
    "혜택 실화냐",
    "바이럴을 유도한다",
    "참여율을 높인다",
    "무조건 높은 혜택",
    "피해야 한다",
    "표현은 피해야",
]


def clip_text(text: str, max_chars: int = 12000) -> str:
    text = str(text or "").strip()

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rstrip() + "\n\n...[내용이 길어 일부 생략됨]"


def remove_prompt_leak_text(text: str) -> str:
    if not text:
        return text

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        if any(pattern in stripped for pattern in LEAK_PATTERNS):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def clean_universal_document_text(
    document: TranslatedUniversalDocument,
) -> TranslatedUniversalDocument:
    document.title = remove_prompt_leak_text(document.title)
    document.summary = remove_prompt_leak_text(document.summary)

    for block in document.blocks:
        block.title = remove_prompt_leak_text(block.title)
        block.text = remove_prompt_leak_text(block.text)

        block.items = [
            cleaned
            for item in block.items
            if (cleaned := remove_prompt_leak_text(item))
        ]

        cleaned_rows = []
        for row in block.rows:
            cleaned_row = [
                remove_prompt_leak_text(cell)
                for cell in row
            ]
            cleaned_rows.append(cleaned_row)

        block.rows = cleaned_rows

    return document


def review_result_to_text(review: TranslationReviewResult) -> str:
    lines = []

    lines.append("번역 검수 결과")
    lines.append("=" * 60)
    lines.append(f"대상 국가: {review.target_country}")
    lines.append(f"대상 언어: {review.target_language}")
    lines.append(f"전체 점수: {review.overall_score}/100")
    lines.append(f"판단: {review.verdict}")
    lines.append("")

    lines.append("[역번역 요약]")
    lines.append(review.back_translation_summary_ko)
    lines.append("")

    lines.append("[한국어 역번역문]")
    lines.append(review.back_translated_document_ko)
    lines.append("")

    lines.append("[잘 번역된 점]")
    if review.good_points:
        for item in review.good_points:
            lines.append(f"- {item}")
    else:
        lines.append("- 특별히 기록된 항목 없음")
    lines.append("")

    lines.append("[문제 목록]")
    if review.issues:
        for idx, issue in enumerate(review.issues, start=1):
            lines.append(f"{idx}. [{issue.category}] {issue.reason}")
            if issue.original_part:
                lines.append(f"   - 원문: {issue.original_part}")
            if issue.translated_part:
                lines.append(f"   - 번역/역번역: {issue.translated_part}")
            if issue.suggestion:
                lines.append(f"   - 수정 제안: {issue.suggestion}")
    else:
        lines.append("- 큰 문제 없음")
    lines.append("")

    lines.append("[누락/추가 내용 검토]")
    lines.append(review.missing_or_added_content or "특이사항 없음")
    lines.append("")

    lines.append("[용어 검토]")
    lines.append(review.terminology_notes or "특이사항 없음")
    lines.append("")

    lines.append("[형식 검토]")
    lines.append(review.format_notes or "특이사항 없음")
    lines.append("")

    lines.append("[최종 의견]")
    lines.append(review.final_comment or "최종 의견 없음")

    return "\n".join(lines)


class UniversalDocumentPipeline:
    def __init__(self):
        settings = get_settings()

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.1,
        )

    def parse_document(
        self,
        text: str,
        source_language_ko: str = "한국어",
    ) -> UniversalDocument:
        structured_llm = self.llm.with_structured_output(UniversalDocument)

        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 PDF에서 추출된 텍스트를 공통 문서 블록 구조로 변환하는 "
                        "문서 분석 Agent입니다."
                    )
                ),
                HumanMessage(
                    content=UNIVERSAL_PARSE_PROMPT.format(
                        text=text,
                        source_language_ko=source_language_ko,
                    )
                ),
            ]
        )

        return result

    def translate_document(
        self,
        document: UniversalDocument,
        target_country: str,
        output_style: str,
    ) -> TranslatedUniversalDocument:
        country = COUNTRY_INFO[target_country]

        document_json = json.dumps(
            document.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        structured_llm = self.llm.with_structured_output(
            TranslatedUniversalDocument
        )

        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 문서 블록 구조를 유지하면서 텍스트만 대상 언어로 번역하는 "
                        "번역 Agent입니다."
                    )
                ),
                HumanMessage(
                    content=UNIVERSAL_TRANSLATE_PROMPT.format(
                        target_country_ko=country["country_ko"],
                        target_language_ko=country["language_ko"],
                        output_style=output_style,
                        document_json=document_json,
                    )
                ),
            ]
        )

        result.target_country = country["country_ko"]
        result.target_language = country["language_ko"]

        result = clean_universal_document_text(result)

        return result

    def translate_document_to_korean(
        self,
        document: UniversalDocument,
        source_country: str,
        output_style: str,
    ) -> TranslatedUniversalDocument:
        country = COUNTRY_INFO[source_country]

        document_json = json.dumps(
            document.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        structured_llm = self.llm.with_structured_output(
            TranslatedUniversalDocument
        )

        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 동남아 언어 문서를 한국어 업무 문서로 자연스럽게 번역하는 "
                        "전문 번역 Agent입니다."
                    )
                ),
                HumanMessage(
                    content=TRANSLATE_TO_KOREAN_PROMPT.format(
                        source_country_ko=country["country_ko"],
                        source_language_ko=country["language_ko"],
                        output_style=output_style,
                        document_json=document_json,
                    )
                ),
            ]
        )

        result.target_country = "한국"
        result.target_language = "한국어"

        result = clean_universal_document_text(result)

        return result

    def review_translation(
        self,
        original_text: str,
        translated_document: TranslatedUniversalDocument,
        target_country: str,
    ) -> TranslationReviewResult:
        country = COUNTRY_INFO[target_country]

        translated_document_json = json.dumps(
            translated_document.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        structured_llm = self.llm.with_structured_output(
            TranslationReviewResult
        )

        result = structured_llm.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 다국어 번역 결과를 한국어로 역번역하고, "
                        "원문 대비 오역/누락/추가/문체/용어/형식을 검수하는 전문 리뷰어입니다."
                    )
                ),
                HumanMessage(
                    content=TRANSLATION_REVIEW_PROMPT.format(
                        target_country_ko=country["country_ko"],
                        target_language_ko=country["language_ko"],
                        original_text=clip_text(original_text, max_chars=12000),
                        translated_document_json=clip_text(
                            translated_document_json,
                            max_chars=16000,
                        ),
                    )
                ),
            ]
        )

        result.target_country = country["country_ko"]
        result.target_language = country["language_ko"]

        result.back_translation_summary_ko = remove_prompt_leak_text(
            result.back_translation_summary_ko
        )
        result.back_translated_document_ko = remove_prompt_leak_text(
            result.back_translated_document_ko
        )
        result.final_comment = remove_prompt_leak_text(
            result.final_comment
        )

        return result

    def run(
        self,
        text: str,
        target_country: str,
        output_style: str,
    ) -> tuple[UniversalDocument, TranslatedUniversalDocument]:
        parsed_document = self.parse_document(
            text=text,
            source_language_ko="한국어",
        )

        translated_document = self.translate_document(
            document=parsed_document,
            target_country=target_country,
            output_style=output_style,
        )

        return parsed_document, translated_document

    def run_to_korean(
        self,
        text: str,
        source_country: str,
        output_style: str,
    ) -> tuple[UniversalDocument, TranslatedUniversalDocument]:
        country = COUNTRY_INFO[source_country]

        parsed_document = self.parse_document(
            text=text,
            source_language_ko=country["language_ko"],
        )

        translated_document = self.translate_document_to_korean(
            document=parsed_document,
            source_country=source_country,
            output_style=output_style,
        )

        return parsed_document, translated_document