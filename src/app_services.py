from schemas import AgentRequest
from pdf_utils import extract_text_from_pdf_bytes, check_pdf_text_quality
from universal_document_pipeline import review_result_to_text
from universal_pdf_renderer import make_universal_report_pdf


def extract_pdf_text_from_upload(uploaded_file):
    pdf_bytes = uploaded_file.getvalue()
    text = extract_text_from_pdf_bytes(pdf_bytes)
    ok, message = check_pdf_text_quality(text)
    return text, ok, message


def run_text_translation(agent, text: str, target_country: str, output_style: str):
    request = AgentRequest(
        text=text,
        target_country=target_country,
        output_style=output_style,
    )
    return agent.run(request)


def run_forward_pdf_translation(
    pipeline,
    extracted_text: str,
    target_country: str,
    output_style: str,
):
    return pipeline.run(
        text=extracted_text,
        target_country=target_country,
        output_style=output_style,
    )


def run_reverse_pdf_translation(
    pipeline,
    extracted_text: str,
    source_country: str,
    output_style: str,
):
    return pipeline.run_to_korean(
        text=extracted_text,
        source_country=source_country,
        output_style=output_style,
    )


def generate_translated_pdf(document, original_filename: str):
    return make_universal_report_pdf(
        document=document,
        original_filename=original_filename,
    )


def run_translation_review(
    pipeline,
    original_text: str,
    translated_document,
    target_country: str,
):
    review_result = pipeline.review_translation(
        original_text=original_text,
        translated_document=translated_document,
        target_country=target_country,
    )
    review_text = review_result_to_text(review_result)
    return review_result, review_text


def run_pdf_summary(agent, extracted_text: str, target_country: str):
    if not hasattr(agent, "summarize_pdf_text"):
        raise AttributeError(
            "현재 agent.py에 summarize_pdf_text() 메서드가 없습니다."
        )

    return agent.summarize_pdf_text(
        text=extracted_text,
        target_country=target_country,
    )