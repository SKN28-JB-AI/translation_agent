import streamlit as st

from services.app_services import (
    extract_pdf_text_from_upload,
    run_text_translation,
    run_forward_pdf_translation,
    run_reverse_pdf_translation,
    generate_translated_pdf,
    run_translation_review,
    run_pdf_summary,
)


COUNTRY_OPTIONS = {
    "vietnam": "베트남",
    "cambodia": "캄보디아",
    "myanmar": "미얀마",
}


MODE_OPTIONS = [
    "텍스트 입력 번역",
    "보고서 PDF 번역 다운로드",
    "동남아어 PDF 한국어 번역",
    "보고서 PDF 요약",
    "보조: Vision PDF 분석",
]


def clear_state_by_prefix(prefix: str):
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]


def render_pdf_reader(uploaded_file, preview_key: str) -> str:
    with st.spinner("PDF에서 텍스트를 추출하는 중입니다..."):
        text, ok, message = extract_pdf_text_from_upload(uploaded_file)

    if ok:
        st.success(message)
    else:
        st.warning(message)
        st.info("텍스트가 제대로 추출되지 않으면 `보조: Vision PDF 분석` 모드를 사용하세요.")

    with st.expander("추출된 텍스트 미리보기", expanded=False):
        st.text_area(
            "추출 결과",
            value=text[:12000],
            height=400,
            key=preview_key,
        )

    return text


def render_document_preview(document, direction_text: str | None = None):
    st.markdown("## 문서 제목")
    st.write(document.title)

    st.markdown("## 문서 유형")
    st.write(document.document_type)

    st.markdown("## 레이아웃 스타일")
    st.write(document.layout_style)

    if direction_text:
        st.markdown("## 번역 방향")
        st.write(direction_text)
    else:
        st.markdown("## 대상 국가 / 언어")
        st.write(f"{document.target_country} / {document.target_language}")

    st.markdown("## 요약")
    st.write(document.summary)

    st.markdown("## 블록 미리보기")

    for block in document.blocks:
        title = block.title or block.text[:30]
        st.markdown(f"### [{block.type}] {title}")

        if block.text and block.type not in ["title", "section"]:
            st.write(block.text)

        for item in block.items:
            st.write(f"- {item}")

        if block.rows:
            st.table(block.rows)


def render_pdf_generate_tab(
    document,
    prefix: str,
    download_filename: str,
    info_text: str,
):
    st.info(info_text)

    if st.button("PDF 생성", key=f"{prefix}_generate_pdf_button"):
        try:
            with st.spinner("PDF를 생성하는 중입니다..."):
                pdf_output = generate_translated_pdf(
                    document=document,
                    original_filename=st.session_state[f"{prefix}_original_filename"],
                )

            st.session_state[f"{prefix}_pdf_bytes"] = pdf_output
            st.success("PDF 생성 완료")

        except Exception as e:
            st.error("PDF 생성 중 오류가 발생했습니다.")
            st.exception(e)

    if f"{prefix}_pdf_bytes" in st.session_state:
        st.download_button(
            label="PDF 다운로드",
            data=st.session_state[f"{prefix}_pdf_bytes"],
            file_name=download_filename,
            mime="application/pdf",
            key=f"{prefix}_download_pdf",
        )


def render_review_tab(
    pipeline,
    document,
    prefix: str,
    fallback_country: str,
):
    st.info(
        "번역 검수는 번역문을 다시 한국어로 해석한 뒤, "
        "원문과 비교하여 오역·누락·추가·문체·용어 문제를 확인합니다."
    )

    if st.button("번역 검수 실행", type="primary", key=f"{prefix}_review_button"):
        try:
            original_text = st.session_state.get(f"{prefix}_original_text", "")
            target_country = st.session_state.get(f"{prefix}_target_country", fallback_country)

            with st.spinner("번역 결과를 역번역하고 원문과 비교 검수하는 중입니다..."):
                review_result, review_text = run_translation_review(
                    pipeline=pipeline,
                    original_text=original_text,
                    translated_document=document,
                    target_country=target_country,
                )

            st.session_state[f"{prefix}_translation_review"] = review_result
            st.session_state[f"{prefix}_translation_review_text"] = review_text
            st.success("번역 검수 완료")

        except Exception as e:
            st.error("번역 검수 중 오류가 발생했습니다.")
            st.exception(e)

    review_key = f"{prefix}_translation_review"
    review_text_key = f"{prefix}_translation_review_text"

    if review_key not in st.session_state:
        return

    review_result = st.session_state[review_key]

    st.markdown("## 검수 요약")
    st.metric("번역 품질 점수", f"{review_result.overall_score}/100")

    st.markdown("### 전체 판단")
    st.write(review_result.verdict)

    st.markdown("### 역번역 요약")
    st.write(review_result.back_translation_summary_ko)

    st.markdown("### 한국어 역번역문")
    st.text_area(
        "번역문을 한국어로 되돌려 해석한 내용",
        value=review_result.back_translated_document_ko,
        height=300,
        key=f"{prefix}_back_translation_area",
    )

    st.markdown("### 잘 번역된 점")
    if review_result.good_points:
        for item in review_result.good_points:
            st.write(f"- {item}")
    else:
        st.write("- 특별히 기록된 항목 없음")

    st.markdown("### 문제 목록")
    if review_result.issues:
        for idx, issue in enumerate(review_result.issues, start=1):
            with st.expander(f"{idx}. [{issue.category}] {issue.reason}"):
                if issue.original_part:
                    st.markdown("**원문 부분**")
                    st.write(issue.original_part)

                if issue.translated_part:
                    st.markdown("**번역/역번역 부분**")
                    st.write(issue.translated_part)

                if issue.suggestion:
                    st.markdown("**수정 제안**")
                    st.write(issue.suggestion)
    else:
        st.success("큰 문제는 발견되지 않았습니다.")

    st.markdown("### 누락/추가 내용 검토")
    st.write(review_result.missing_or_added_content or "특이사항 없음")

    st.markdown("### 용어 검토")
    st.write(review_result.terminology_notes or "특이사항 없음")

    st.markdown("### 형식 검토")
    st.write(review_result.format_notes or "특이사항 없음")

    st.markdown("### 최종 의견")
    st.write(review_result.final_comment or "최종 의견 없음")

    if review_text_key in st.session_state:
        st.download_button(
            label="번역 검수 결과 TXT 다운로드",
            data=st.session_state[review_text_key].encode("utf-8"),
            file_name="translation_review_result.txt",
            mime="text/plain",
            key=f"{prefix}_review_txt_download",
        )


def render_text_mode(agent, target_country: str, output_style: str):
    st.markdown("## 한국어 텍스트 → 동남아 언어 번역")

    sample_text = """신규 고객을 대상으로 모바일 금융 서비스의 주요 혜택을 소개하는 캠페인을 기획한다.
숏폼 콘텐츠와 카드뉴스를 활용해 서비스 접근성을 높이고, 과장된 수익 보장 표현은 사용하지 않는다."""

    text = st.text_area(
        "번역할 한국어 광고/마케팅 기획서를 입력하세요.",
        value=sample_text,
        height=260,
    )

    if not st.button("RAG 번역 Agent 실행", type="primary"):
        return

    if not text.strip():
        st.warning("번역할 내용을 입력하세요.")
        return

    try:
        with st.spinner("RAG 검색, 용어 감지, 번역, 현지화 메모 생성 중입니다..."):
            response = run_text_translation(
                agent=agent,
                text=text,
                target_country=target_country,
                output_style=output_style,
            )

        st.success(f"{response.target_country_ko} / {response.target_language_ko} 번역 완료")

        tab1, tab2, tab3 = st.tabs(["최종 결과", "정확 매칭", "RAG 검색 근거"])

        with tab1:
            st.markdown(response.result_markdown)

        with tab2:
            st.code(response.exact_matches, language="text")

        with tab3:
            st.code(response.retrieved_context, language="text")

    except Exception as e:
        st.error("실행 중 오류가 발생했습니다.")
        st.exception(e)


def render_forward_pdf_mode(pipeline, target_country: str, output_style: str):
    st.markdown("## 한국어 보고서 PDF → 동남아 언어 번역")

    uploaded_file = st.file_uploader(
        "번역할 보고서형 PDF를 업로드하세요.",
        type=["pdf"],
        help="텍스트 선택이 가능한 PDF를 권장합니다.",
        key="universal_pdf_uploader",
    )

    if uploaded_file is None:
        return

    extracted_text = render_pdf_reader(uploaded_file, "universal_extracted_preview")
    st.markdown("---")

    if st.button(
        "공통 문서 구조 분석 + 번역 실행",
        type="primary",
        disabled=not bool(extracted_text.strip()),
        key="universal_translate_button",
    ):
        try:
            with st.spinner("문서를 공통 블록 구조로 분석하고 번역하는 중입니다..."):
                parsed_document, translated_document = run_forward_pdf_translation(
                    pipeline=pipeline,
                    extracted_text=extracted_text,
                    target_country=target_country,
                    output_style=output_style,
                )

            st.session_state["universal_original_text"] = extracted_text
            st.session_state["universal_parsed_document"] = parsed_document
            st.session_state["universal_translated_document"] = translated_document
            st.session_state["universal_original_filename"] = uploaded_file.name
            st.session_state["universal_target_country"] = target_country

            for key in [
                "universal_pdf_bytes",
                "universal_translation_review",
                "universal_translation_review_text",
            ]:
                st.session_state.pop(key, None)

            st.success("공통 문서 구조 분석 및 번역 완료")

        except Exception as e:
            st.error("공통 문서 구조 분석 또는 번역 중 오류가 발생했습니다.")
            st.exception(e)

    if "universal_translated_document" not in st.session_state:
        return

    document = st.session_state["universal_translated_document"]

    tab1, tab2, tab3, tab4 = st.tabs(
        ["번역 구조 미리보기", "JSON 확인", "PDF 생성", "번역 검수"]
    )

    with tab1:
        render_document_preview(document)

    with tab2:
        st.json(document.model_dump())

    with tab3:
        render_pdf_generate_tab(
            document=document,
            prefix="universal",
            download_filename="translated_universal_report.pdf",
            info_text="공통 블록 구조를 기반으로 번역 PDF를 생성합니다.",
        )

    with tab4:
        render_review_tab(
            pipeline=pipeline,
            document=document,
            prefix="universal",
            fallback_country=target_country,
        )


def render_reverse_pdf_mode(pipeline):
    st.markdown("## 동남아어 PDF → 한국어 번역")

    source_country = st.selectbox(
        "원문 국가/언어 선택",
        ["vietnam", "cambodia", "myanmar"],
        format_func=lambda x: COUNTRY_OPTIONS[x],
        key="reverse_source_country",
    )

    korean_output_style = st.selectbox(
        "한국어 번역 문체",
        ["업무 보고서체", "자연스러운 설명체", "간결한 요약체", "마케팅 기획서체"],
        key="reverse_korean_output_style",
    )

    uploaded_file = st.file_uploader(
        "한국어로 번역할 동남아어 PDF를 업로드하세요.",
        type=["pdf"],
        help="텍스트 선택이 가능한 PDF를 권장합니다.",
        key="reverse_pdf_uploader",
    )

    if uploaded_file is None:
        return

    extracted_text = render_pdf_reader(uploaded_file, "reverse_extracted_preview")
    st.markdown("---")

    if st.button(
        "동남아어 문서 구조 분석 + 한국어 번역 실행",
        type="primary",
        disabled=not bool(extracted_text.strip()),
        key="reverse_translate_button",
    ):
        try:
            with st.spinner("동남아어 문서를 분석하고 한국어로 번역하는 중입니다..."):
                parsed_document, translated_document = run_reverse_pdf_translation(
                    pipeline=pipeline,
                    extracted_text=extracted_text,
                    source_country=source_country,
                    output_style=korean_output_style,
                )

            st.session_state["reverse_original_text"] = extracted_text
            st.session_state["reverse_parsed_document"] = parsed_document
            st.session_state["reverse_translated_document"] = translated_document
            st.session_state["reverse_original_filename"] = uploaded_file.name
            st.session_state["reverse_source_country"] = source_country
            st.session_state.pop("reverse_pdf_bytes", None)

            st.success("한국어 번역 완료")

        except Exception as e:
            st.error("동남아어 → 한국어 번역 중 오류가 발생했습니다.")
            st.exception(e)

    if "reverse_translated_document" not in st.session_state:
        return

    document = st.session_state["reverse_translated_document"]
    direction = f"{COUNTRY_OPTIONS.get(source_country, source_country)} → 한국어"

    tab1, tab2, tab3 = st.tabs(["한국어 번역 미리보기", "JSON 확인", "한국어 PDF 생성"])

    with tab1:
        render_document_preview(document, direction_text=direction)

    with tab2:
        st.json(document.model_dump())

    with tab3:
        render_pdf_generate_tab(
            document=document,
            prefix="reverse",
            download_filename="translated_to_korean_report.pdf",
            info_text="동남아어 문서 구조를 유지한 상태로 한국어 PDF를 생성합니다.",
        )


def render_summary_mode(agent, target_country: str):
    st.markdown("## 보고서 PDF 요약")

    uploaded_file = st.file_uploader(
        "요약할 PDF를 업로드하세요.",
        type=["pdf"],
        key="summary_pdf_uploader",
    )

    if uploaded_file is None:
        return

    extracted_text = render_pdf_reader(uploaded_file, "summary_extracted_preview")

    if not st.button(
        "PDF 요약 실행",
        type="primary",
        disabled=not bool(extracted_text.strip()),
        key="summary_button",
    ):
        return

    try:
        with st.spinner("PDF 내용을 요약하는 중입니다..."):
            summary = run_pdf_summary(
                agent=agent,
                extracted_text=extracted_text,
                target_country=target_country,
            )

        st.markdown("## 요약 결과")
        st.markdown(summary)

        st.download_button(
            label="요약 결과 TXT 다운로드",
            data=str(summary).encode("utf-8"),
            file_name="pdf_summary.txt",
            mime="text/plain",
            key="summary_txt_download",
        )

    except AttributeError as e:
        st.warning(str(e))

    except Exception as e:
        st.error("PDF 요약 중 오류가 발생했습니다.")
        st.exception(e)


def render_vision_mode():
    st.markdown("## 보조: Vision PDF 분석")

    st.info(
        "이 모드는 이미지형 PDF나 PPT형 PDF처럼 일반 텍스트 추출이 어려운 문서를 확인하기 위한 보조 기능입니다. "
        "현재 메인 번역 기능은 텍스트 선택 가능한 PDF에 최적화되어 있습니다."
    )

    uploaded_file = st.file_uploader(
        "분석할 이미지형/PPT형 PDF를 업로드하세요.",
        type=["pdf"],
        key="vision_pdf_uploader",
    )

    if uploaded_file is None:
        return

    st.warning(
        "이미지형 PDF는 pypdf 텍스트 추출만으로는 정확도가 낮을 수 있습니다. "
        "텍스트가 추출되지 않으면 Vision 분석 또는 원본 문서 파일 사용이 필요합니다."
    )

    try:
        extracted_text = render_pdf_reader(uploaded_file, "vision_extracted_preview")

        if extracted_text.strip():
            st.success("일부 텍스트가 추출되었습니다. 일반 PDF 번역 모드에서 시도할 수 있습니다.")
        else:
            st.error("텍스트가 거의 추출되지 않았습니다. 이미지형/PPT형 PDF일 가능성이 큽니다.")

    except Exception as e:
        st.error("PDF 텍스트 확인 중 오류가 발생했습니다.")
        st.exception(e)