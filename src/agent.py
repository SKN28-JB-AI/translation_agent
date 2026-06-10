from openai import OpenAI

from config import get_settings
from data_loader import load_all_data
from prompts import SYSTEM_PROMPT, build_user_prompt, COUNTRY_INFO
from retriever import SimpleCSVRetriever
from schemas import AgentRequest, AgentResponse


class MarketBridgeAgent:
    """
    광고/마케팅 기획서 번역 Agent MVP.

    현재 구조:
    1. CSV 데이터 로드
    2. 입력 텍스트에서 마케팅 용어/은어/금융 용어/위험 표현 검색
    3. 검색 결과를 LLM 프롬프트에 포함
    4. 대상 국가 언어로 기획서 번역
    5. 현지화 메모와 검토 결과 생성
    """

    def __init__(self):
        self.settings = get_settings()

        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
        )

        self.data = load_all_data()
        self.retriever = SimpleCSVRetriever(self.data)

    def run(self, request: AgentRequest) -> AgentResponse:
        if request.target_country not in COUNTRY_INFO:
            raise ValueError(
                "지원하지 않는 국가입니다. vietnam, cambodia, myanmar 중 하나를 선택하세요."
            )

        context = self.retriever.build_context(request.text)

        user_prompt = build_user_prompt(
            text=request.text,
            target_country=request.target_country,
            output_style=request.output_style,
            context=context,
        )

        result = self._call_llm(user_prompt)

        country = COUNTRY_INFO[request.target_country]

        detected_summary = self._build_detected_summary(context)

        return AgentResponse(
            result_markdown=result,
            target_country=country["country_ko"],
            target_language=country["language_ko"],
            has_risk_expression=context["has_risk_expression"],
            detected_summary=detected_summary,
        )

    def _call_llm(self, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    def _build_detected_summary(self, context: dict[str, str]) -> str:
        return "\n\n".join(
            [
                context["marketing_terms"],
                context["slang_terms"],
                context["finance_terms"],
                context["risk_expressions"],
            ]
        )


if __name__ == "__main__":
    agent = MarketBridgeAgent()

    sample_text = """
이번 캠페인은 Z세대가 반응할 수 있는 “혜택 실화냐”식 메시지를 활용해 바이럴을 유도한다.
특히 숏폼 콘텐츠에서는 갓성비 이미지를 강조하고, 댓글 유도형 콘텐츠를 통해 참여율을 높인다.
단, 무조건 높은 혜택을 제공한다는 식의 표현은 피해야 한다.
"""

    request = AgentRequest(
        text=sample_text,
        target_country="vietnam",
        output_style="기획서 문체",
    )

    response = agent.run(request)
    print(response.result_markdown)