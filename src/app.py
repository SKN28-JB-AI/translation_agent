import streamlit as st

from agent import MarketBridgeRAGAgent
from universal_document_pipeline import UniversalDocumentPipeline

from app_pages import (
    COUNTRY_OPTIONS,
    MODE_OPTIONS,
    clear_state_by_prefix,
    render_text_mode,
    render_forward_pdf_mode,
    render_reverse_pdf_mode,
    render_summary_mode,
    render_vision_mode,
)


st.set_page_config(
    page_title="MarketBridge-AI",
    page_icon="🌏",
    layout="wide",
)


@st.cache_resource
def load_agent():
    return MarketBridgeRAGAgent()


@st.cache_resource
def load_universal_pipeline():
    return UniversalDocumentPipeline()


st.title("🌏 MarketBridge-AI")
st.subheader("동남아 현지 담당자를 위한 광고/마케팅 기획서 번역·현지화 Agent")

st.markdown(
    """
이 앱은 한국어 광고·마케팅 문서를 동남아 언어로 번역하거나,  
반대로 동남아 언어 문서를 한국어로 번역하는 기능을 제공합니다.
"""
)


with st.sidebar:
    st.header("설정")

    mode = st.radio("기능 선택", MODE_OPTIONS)

    st.markdown("---")

    target_country = st.selectbox(
        "대상 국가",
        options=list(COUNTRY_OPTIONS.keys()),
        format_func=lambda x: COUNTRY_OPTIONS[x],
        key="sidebar_target_country",
    )

    output_style = st.selectbox(
        "번역 문체",
        options=[
            "기획서 문체",
            "공식 보고서 문체",
            "현지 담당자가 이해하기 쉬운 설명형 문체",
            "마케팅 기획서체",
            "간결한 요약체",
        ],
        key="sidebar_output_style",
    )

    st.markdown("---")

    if st.button("현재 작업 상태 초기화"):
        clear_state_by_prefix("universal_")
        clear_state_by_prefix("reverse_")
        st.success("작업 상태를 초기화했습니다.")

    st.caption("PDF 번역은 텍스트 선택 가능한 PDF에서 가장 안정적으로 동작합니다.")


agent = load_agent()
pipeline = load_universal_pipeline()


if mode == "텍스트 입력 번역":
    render_text_mode(
        agent=agent,
        target_country=target_country,
        output_style=output_style,
    )

elif mode == "보고서 PDF 번역 다운로드":
    render_forward_pdf_mode(
        pipeline=pipeline,
        target_country=target_country,
        output_style=output_style,
    )

elif mode == "동남아어 PDF 한국어 번역":
    render_reverse_pdf_mode(
        pipeline=pipeline,
    )

elif mode == "보고서 PDF 요약":
    render_summary_mode(
        agent=agent,
        target_country=target_country,
    )

elif mode == "보조: Vision PDF 분석":
    render_vision_mode()