from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.config import get_settings
from core.prompts import (
    COUNTRY_INFO,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    SIMPLE_TRANSLATION_PROMPT,
)

from models.schemas import AgentRequest, AgentResponse

from rag.rag_retriever import SafeRAGRetriever, format_docs
from rag.exact_matcher import build_exact_match_context


class MarketBridgeRAGAgent:
    def __init__(self):
        settings = get_settings()

        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=0.2,
        )

        self.retriever = SafeRAGRetriever()

    def _get_country(self, country_key: str) -> dict:
        if country_key not in COUNTRY_INFO:
            raise ValueError(
                f"지원하지 않는 국가 코드입니다: {country_key}. "
                "vietnam, cambodia, myanmar 중 하나를 사용하세요."
            )

        return COUNTRY_INFO[country_key]

    def run(self, request: AgentRequest) -> AgentResponse:
        """
        텍스트 입력 번역 기능입니다.

        task_type:
        - simple_translation: 단순 번역
        - document_translation: 문서 번역 + RAG + 용어 매칭
        """
        country = self._get_country(request.target_country)

        task_type = getattr(request, "task_type", "simple_translation")

        if task_type == "simple_translation":
            return self._run_simple_translation(
                request=request,
                country=country,
            )

        if task_type == "document_translation":
            return self._run_document_translation(
                request=request,
                country=country,
            )

        raise ValueError(
            f"지원하지 않는 task_type입니다: {task_type}. "
            "simple_translation 또는 document_translation을 사용하세요."
        )

    def _run_simple_translation(
        self,
        request: AgentRequest,
        country: dict,
    ) -> AgentResponse:
        """
        짧은 문장이나 일반 문장을 단순 번역합니다.
        RAG 검색, 정확 매칭, 현지화 분석을 사용하지 않습니다.
        """
        prompt = SIMPLE_TRANSLATION_PROMPT.format(
            target_language_ko=country["language_ko"],
            target_country_ko=country["country_ko"],
            text=request.text,
        )

        response = self.llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )

        return AgentResponse(
            result_markdown=response.content.strip(),
            retrieved_context="",
            exact_matches="",
            target_country_ko=country["country_ko"],
            target_language_ko=country["language_ko"],
        )

    def _run_document_translation(
        self,
        request: AgentRequest,
        country: dict,
    ) -> AgentResponse:
        """
        마케팅/금융 문서성 텍스트 번역 기능입니다.
        정확 매칭과 RAG 검색 결과를 내부 참고자료로 사용합니다.
        """
        exact_matches = build_exact_match_context(request.text)

        query = (
            f"대상 국가: {country['country_ko']}\n"
            f"광고 마케팅 문서 번역 현지화 금융 표현 위험 표현 마케팅 용어\n"
            f"원문: {request.text}"
        )

        retrieved_docs = self.retriever.retrieve(
            query=query,
            target_country=request.target_country,
            k=5,
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
            result_markdown=response.content.strip(),
            retrieved_context=retrieved_context,
            exact_matches=exact_matches,
            target_country_ko=country["country_ko"],
            target_language_ko=country["language_ko"],
        )