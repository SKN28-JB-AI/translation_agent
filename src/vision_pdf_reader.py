import base64
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from openai import OpenAI

from config import get_settings


def render_pdf_page_to_png_bytes(page, zoom: float = 2.5) -> bytes:
    """
    PDF 한 페이지를 PNG 이미지 bytes로 변환합니다.
    zoom이 높을수록 글자가 잘 보이지만 비용과 처리 시간이 증가합니다.
    """
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)
    return pix.tobytes("png")


def image_bytes_to_data_url(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def compress_image_bytes(image_bytes: bytes, max_width: int = 1600) -> bytes:
    """
    이미지 크기를 줄여 Vision API 비용과 속도를 조절합니다.
    """
    image = Image.open(BytesIO(image_bytes)).convert("RGB")

    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height))

    output = BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue()


def extract_page_markdown_with_vision(
    image_bytes: bytes,
    page_number: int,
    target_purpose: str = "summary",
) -> str:
    """
    페이지 이미지를 Vision 모델로 읽어 Markdown 텍스트로 재구성합니다.
    """
    settings = get_settings()

    vision_model = getattr(settings, "vision_model", None)
    if not vision_model:
        vision_model = "gpt-4.1-mini"

    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    compressed = compress_image_bytes(image_bytes)
    data_url = image_bytes_to_data_url(compressed)

    prompt = f"""
당신은 광고/마케팅 기획서 PDF를 읽는 문서 분석 Agent입니다.

아래 이미지는 기획서 PDF의 {page_number}페이지입니다.
이미지 안의 텍스트, 제목, 도표, 핵심 메시지, 기획 의도를 읽어서 Markdown으로 재구성하세요.

중요 규칙:
1. 보이는 텍스트를 최대한 정확히 옮기세요.
2. 작은 글씨가 불확실하면 [불확실]이라고 표시하세요.
3. 단순 OCR처럼 줄만 나열하지 말고, 기획서 구조로 정리하세요.
4. 표/도표/스토리보드가 있으면 내용을 설명하세요.
5. 광고 기획서 관점에서 핵심 메시지와 페이지 역할을 요약하세요.
6. 없는 내용을 지어내지 마세요.

출력 형식:

# Page {page_number}

## 페이지 역할
...

## 추출 텍스트
...

## 도표/이미지 설명
...

## 핵심 요약
...
"""

    response = client.chat.completions.create(
        model=vision_model,
        messages=[
            {
                "role": "system",
                "content": "당신은 이미지 기반 PDF 기획서를 Markdown으로 구조화하는 문서 분석 전문가입니다.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url,
                        },
                    },
                ],
            },
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content


def extract_pdf_markdown_with_vision(
    pdf_bytes: bytes,
    max_pages: int | None = None,
    zoom: float = 2.5,
) -> str:
    """
    PDF 전체를 페이지별 이미지로 변환한 뒤 Vision 모델로 Markdown 추출합니다.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    total_pages = len(doc)
    if max_pages is not None:
        total_pages = min(total_pages, max_pages)

    page_results = []

    for page_idx in range(total_pages):
        page = doc[page_idx]
        page_number = page_idx + 1

        image_bytes = render_pdf_page_to_png_bytes(page, zoom=zoom)

        page_markdown = extract_page_markdown_with_vision(
            image_bytes=image_bytes,
            page_number=page_number,
        )

        page_results.append(page_markdown)

    doc.close()

    return "\n\n---\n\n".join(page_results)