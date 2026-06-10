import streamlit as st

from agent import MarketBridgeAgent
from schemas import AgentRequest


st.set_page_config(
    page_title="MarketBridge-AI",
    page_icon="🌏",
    layout="wide",
)


@st.cache_resource
def load_agent():
    return MarketBridgeAgent()


st.title("🌏 MarketBridge-AI")
st.subheader("동남아 현지 담당자를 위한 광고/마케팅 기획서 번역 Agent")

st.markdown(
    """
한국어 광고·마케팅 기획서를 **베트남어, 크메르어, 미얀마어**로 번역하고,  
기획서 안에 포함된 **마케팅 용어, 밈, 은어, 위험 표현**을 함께 해석합니다.
"""
)

with st.sidebar:
    st.header("설정")

    target_country = st.selectbox(
        "대상 국가",
        options=["vietnam", "cambodia", "myanmar"],
        format_func=lambda x: {
            "vietnam": "베트남",
            "cambodia": "캄보디아",
            "myanmar": "미얀마",
        }[x],
    )

    output_style = st.selectbox(
        "번역 문체",
        options=[
            "기획서 문체",
            "공식 보고서 문체",
            "현지 담당자가 이해하기 쉬운 설명형 문체",
        ],
    )

    st.markdown("---")
    st.caption("MVP 버전: CSV 기반 용어 검색 + LLM 번역")


sample_text = """이번 캠페인은 Z세대가 반응할 수 있는 “혜택 실화냐”식 메시지를 활용해 바이럴을 유도한다.
특히 숏폼 콘텐츠에서는 갓성비 이미지를 강조하고, 댓글 유도형 콘텐츠를 통해 참여율을 높인다.
단, 무조건 높은 혜택을 제공한다는 식의 표현은 피해야 한다."""

text = st.text_area(
    "번역할 한국어 광고/마케팅 기획서를 입력하세요.",
    value=sample_text,
    height=250,
)

run_button = st.button("번역 Agent 실행", type="primary")

if run_button:
    if not text.strip():
        st.warning("번역할 내용을 입력하세요.")
    else:
        try:
            agent = load_agent()

            request = AgentRequest(
                text=text,
                target_country=target_country,
                output_style=output_style,
            )

            with st.spinner("Agent가 문서 분석, 용어 감지, 번역, 현지화 메모 생성을 진행 중입니다..."):
                response = agent.run(request)

            st.success(
                f"{response.target_country} / {response.target_language} 번역이 완료되었습니다."
            )

            if response.has_risk_expression:
                st.warning("입력 문서에서 위험 표현 가능성이 있는 문구가 감지되었습니다.")

            tab1, tab2 = st.tabs(["최종 결과", "감지된 참고 정보"])

            with tab1:
                st.markdown(response.result_markdown)

            with tab2:
                st.markdown("### CSV 기반 검색 결과")
                st.code(response.detected_summary or "감지된 항목 없음", language="text")

        except Exception as e:
            st.error("실행 중 오류가 발생했습니다.")
            st.exception(e)