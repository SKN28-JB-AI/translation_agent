from io import BytesIO
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def make_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def make_markdown_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def find_default_font() -> str | None:
    """
    Windows에서 흔히 있는 한글 폰트를 우선 찾습니다.
    크메르어/미얀마어까지 깔끔하게 출력하려면 Noto 계열 폰트를 설치하고 경로를 지정하는 것을 추천합니다.
    """
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return path

    return None


def make_pdf_bytes(
    title: str,
    markdown_text: str,
    font_path: str | None = None,
) -> bytes:
    """
    Markdown 스타일 텍스트를 간단한 PDF 리포트로 변환합니다.

    주의:
    - 원본 PDF 레이아웃을 보존하는 함수가 아닙니다.
    - 번역 결과를 읽기 좋은 리포트 PDF로 만드는 용도입니다.
    - 미얀마어/크메르어가 깨지면 Noto Sans Myanmar, Noto Sans Khmer 같은 폰트 경로를 지정하세요.
    """
    buffer = BytesIO()

    if font_path is None:
        font_path = find_default_font()

    font_name = "Helvetica"

    if font_path and Path(font_path).exists():
        font_name = "CustomUnicodeFont"
        pdfmetrics.registerFont(TTFont(font_name, font_path))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=24,
        spaceAfter=14,
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        spaceAfter=8,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    story = []
    story.append(Paragraph(escape_text(title), title_style))
    story.append(Spacer(1, 8))

    for line in markdown_text.splitlines():
        line = line.strip()

        if not line:
            story.append(Spacer(1, 6))
            continue

        if line.startswith("## "):
            story.append(Paragraph(escape_text(line.replace("## ", "")), heading_style))
        elif line.startswith("# "):
            story.append(Paragraph(escape_text(line.replace("# ", "")), heading_style))
        else:
            story.append(Paragraph(escape_text(line), body_style))

    doc.build(story)

    buffer.seek(0)
    return buffer.read()


def escape_text(text: str) -> str:
    """
    ReportLab Paragraph에서 특수문자 충돌을 막기 위한 간단한 escape.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )