from io import BytesIO
from pypdf import PdfReader


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    보고서형 PDF에서 텍스트를 추출합니다.

    대상:
    - Word, 한글, Google Docs, Notion 등에서 저장한 PDF
    - 마우스로 텍스트 선택이 가능한 PDF

    비대상:
    - 스캔 PDF
    - 이미지형 PPT PDF
    - 사진으로 찍은 문서
    """
    reader = PdfReader(BytesIO(pdf_bytes))

    page_texts = []

    for page_idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()

        if text:
            page_texts.append(f"\n\n# Page {page_idx}\n\n{text}")

    return "\n".join(page_texts).strip()


def check_pdf_text_quality(text: str, min_chars: int = 300) -> tuple[bool, str]:
    """
    pypdf로 추출한 텍스트 품질을 확인합니다.
    """
    cleaned = text.strip()

    if not cleaned:
        return (
            False,
            "PDF에서 텍스트를 추출하지 못했습니다. 이미지형/PPT형/스캔 PDF일 가능성이 큽니다.",
        )

    if len(cleaned) < min_chars:
        return (
            False,
            f"추출된 텍스트가 너무 짧습니다. 현재 {len(cleaned)}자만 추출되었습니다. 이미지형 PDF일 수 있습니다.",
        )

    return (
        True,
        f"보고서형 PDF 텍스트 추출 성공: 약 {len(cleaned):,}자 추출",
    )


def split_text_by_length(
    text: str,
    max_chars: int = 3500,
    overlap_chars: int = 300,
) -> list[str]:
    """
    긴 문서를 LLM에 넣기 위해 글자 수 기준으로 나눕니다.
    """
    text = text.strip()

    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        candidate = current + "\n" + paragraph if current else paragraph

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)

            if len(paragraph) > max_chars:
                start = 0

                while start < len(paragraph):
                    end = start + max_chars
                    chunks.append(paragraph[start:end])

                    next_start = end - overlap_chars

                    if next_start <= start:
                        break

                    start = next_start
            else:
                current = paragraph

    if current:
        chunks.append(current)

    return chunks