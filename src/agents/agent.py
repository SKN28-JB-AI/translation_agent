from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import get_settings
from core.prompts import (
    COUNTRY_INFO,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE
)

from documents.pdf_utils import split_text_by_length
from models.schemas import AgentRequest, AgentResponse
from rag.rag_retriever import format_docs
from rag.rag_retriever import SafeRAGRetriever as MarketBridgeRetriever
from rag.exact_matcher import build_exact_match_context


PDF_TRANSLATION_ONLY_PROMPT = """
다음은 보고서형 PDF에서 추출한 한국어 텍스트입니다.
이 텍스트를 {target_language_ko}로 번역하세요.

[대상 국가]
{target_country_ko}

[대상 언어]
{target_language_ko}

[번역 문체]
{output_style}

[정확 매칭으로 감지된 표현]
{exact_matches}

[RAG 검색 참고자료]
{retrieved_context}

[번역할 원문]
{text}

[중요 지시]
- 번역 결과만 작성하세요.
- 별도의 한국어 설명, 현지화 메모, 위험 표현 검토 섹션을 추가하지 마세요.
- 원문의 제목, 소제목, 목록, 페이지 구분은 최대한 유지하세요.
- '# Page 1' 같은 페이지 구분은 그대로 유지하세요.
- 마케팅 용어와 은어는 직역하지 말고 현지 담당자가 이해하기 자연스럽게 번역하세요.
- 금융/혜택/수익 관련 표현은 보장처럼 들리지 않게 안전하게 번역하세요.
- 표처럼 보이는 내용은 가능한 한 줄 구조를 유지하세요.
- 없는 내용은 추가하지 마세요.
"""


DOCUMENT_SUMMARY_PROMPT = """
다음은 광고/마케팅 기획서 PDF에서 추출한 텍스트입니다.
이 문서를 한국어로 요약하세요.

[대상 국가]
{target_country_ko}

[정확 매칭으로 감지된 표현]
{exact_matches}

[RAG 검색 참고자료]
{retrieved_context}

[문서 내용]
{text}

[요약 지시]
아래 형식을 지켜서 요약하세요.

## 1. 기획안 개요
- 문서의 목적을 요약하세요.

## 2. 핵심 전략
- 캠페인/마케팅 전략의 핵심을 정리하세요.

## 3. 타깃 고객
- 문서에서 추정되는 타깃 고객을 정리하세요.

## 4. 주요 마케팅 용어 및 은어
- 감지된 마케팅 용어, 밈, 은어를 설명하세요.

## 5. 현지화 관점 메모
- {target_country_ko} 현지 담당자가 이해할 때 주의할 점을 정리하세요.

## 6. 위험 표현 검토
- 과장 표현, 보장 표현, 오해 가능 표현이 있으면 정리하세요.
"""


class MarketBridgeRAGAgent:
    def __init__(self):
        settings = get_settings()

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.2,
        )

        self.retriever = MarketBridgeRetriever()

    def run(self, request: AgentRequest) -> AgentResponse:
        """
        기존 텍스트 입력 번역 기능입니다.
        """
        country = COUNTRY_INFO[request.target_country]

        exact_matches = build_exact_match_context(request.text)

        query = (
            f"대상 국가: {country['country_ko']}\n"
            f"광고 마케팅 기획서 번역 현지화 위험 표현 마케팅 용어 밈 은어\n"
            f"원문: {request.text}"
        )

        retrieved_docs = self.retriever.retrieve(
            query=query,
            target_country=request.target_country,
            k=10,
        )

        retrieved_context = format_docs(retrieved_docs)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            target_language_ko=country["language_ko"],
            target_country_ko=country["country_ko"],
            output_style=request.output_style,
            text=request.text,
            exact_matches=exact_matches,
            retrieved_context=retrieved_context,
        )

        response = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ]
        )

        return AgentResponse(
            result_markdown=response.content,
            retrieved_context=retrieved_context,
            exact_matches=exact_matches,
            target_country_ko=country["country_ko"],
            target_language_ko=country["language_ko"],
        )

    def translate_pdf_text(
        self,
        text: str,
        target_country: str,
        output_style: str = "공식 보고서 문체",
    ) -> AgentResponse:
        """
        보고서형 PDF에서 추출한 텍스트를 일반 텍스트 형태로 번역합니다.
        원본 레이아웃 유지 PDF 생성에는 layout_pdf_translator.py를 사용합니다.
        """
        country = COUNTRY_INFO[target_country]

        chunks = split_text_by_length(
            text,
            max_chars=4500,
            overlap_chars=200,
        )

        if not chunks:
            raise ValueError("번역할 텍스트가 없습니다.")

        translated_chunks = []
        all_exact_matches = []
        all_retrieved_contexts = []

        for idx, chunk in enumerate(chunks, start=1):
            exact_matches = build_exact_match_context(chunk)

            query = (
                f"대상 국가: {country['country_ko']}\n"
                f"보고서 PDF 번역 광고 마케팅 기획서 현지화 용어\n"
                f"문서 일부: {chunk}"
            )

            retrieved_docs = self.retriever.retrieve(
                query=query,
                target_country=target_country,
                k=6,
            )

            retrieved_context = format_docs(retrieved_docs)

            prompt = PDF_TRANSLATION_ONLY_PROMPT.format(
                target_language_ko=country["language_ko"],
                target_country_ko=country["country_ko"],
                output_style=output_style,
                exact_matches=exact_matches,
                retrieved_context=retrieved_context,
                text=chunk,
            )

            response = self.llm.invoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
            )

            translated_chunks.append(response.content.strip())
            all_exact_matches.append(f"\n\n# Chunk {idx}\n\n{exact_matches}")
            all_retrieved_contexts.append(f"\n\n# Chunk {idx}\n\n{retrieved_context}")

        final_result = "\n\n".join(translated_chunks)

        return AgentResponse(
            result_markdown=final_result,
            retrieved_context="\n\n".join(all_retrieved_contexts),
            exact_matches="\n\n".join(all_exact_matches),
            target_country_ko=country["country_ko"],
            target_language_ko=country["language_ko"],
        )

    def summarize_pdf_text(
        self,
        text: str,
        target_country: str,
    ) -> AgentResponse:
        """
        PDF에서 추출한 텍스트를 한국어로 요약합니다.
        """
        country = COUNTRY_INFO[target_country]

        max_summary_chars = 12000
        limited_text = text[:max_summary_chars]

        exact_matches = build_exact_match_context(limited_text)

        query = (
            f"대상 국가: {country['country_ko']}\n"
            f"광고 마케팅 기획서 PDF 요약 현지화 위험 표현\n"
            f"문서 내용: {limited_text}"
        )

        retrieved_docs = self.retriever.retrieve(
            query=query,
            target_country=target_country,
            k=10,
        )

        retrieved_context = format_docs(retrieved_docs)

        prompt = DOCUMENT_SUMMARY_PROMPT.format(
            target_country_ko=country["country_ko"],
            exact_matches=exact_matches,
            retrieved_context=retrieved_context,
            text=limited_text,
        )

        response = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )

        final_result = (
            f"# PDF 기획안 요약 결과\n\n"
            f"- 대상 국가 관점: {country['country_ko']}\n"
            f"- 원문 길이: {len(text)}자\n"
            f"- 요약 반영 길이: {len(limited_text)}자\n\n"
            f"{response.content}"
        )

        return AgentResponse(
            result_markdown=final_result,
            retrieved_context=retrieved_context,
            exact_matches=exact_matches,
            target_country_ko=country["country_ko"],
            target_language_ko=country["language_ko"],
        )