import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from universal_document_schema import TranslatedUniversalDocument, UniversalBlock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def normalize_country_key(target_country: str) -> str:
    """
    target_country 값이 한국어/영어/현지어/언어명 등으로 들어와도
    내부에서는 동일한 key로 처리합니다.
    """
    value = str(target_country or "").strip().lower()

    # Korea / Korean
    if value in [
        "한국",
        "대한민국",
        "korea",
        "south korea",
        "republic of korea",
        "korean",
        "한국어",
    ]:
        return "korea"
    
    # Cambodia / Khmer
    if value in [
        "캄보디아",
        "cambodia",
        "kingdom of cambodia",
        "khmer",
        "크메르",
        "크메르어",
        "khmer language",
        "កម្ពុជា",
        "ប្រទេសកម្ពុជា",
        "ព្រះរាជាណាចក្រកម្ពុជា",
        "ខ្មែរ",
        "ភាសាខ្មែរ",
    ]:
        return "cambodia"

    # Myanmar / Burmese
    if value in [
        "미얀마",
        "myanmar",
        "burmese",
        "버마어",
        "미얀마어",
        "myanmar language",
        "မြန်မာ",
        "မြန်မာနိုင်ငံ",
        "မြန်မာဘာသာ",
        "ဗမာ",
        "ဗမာစာ",
    ]:
        return "myanmar"

    # Vietnam / Vietnamese
    if value in [
        "베트남",
        "vietnam",
        "viet nam",
        "vietnamese",
        "베트남어",
        "việt nam",
        "tiếng việt",
    ]:
        return "vietnam"

    return "default"


def resolve_font_path(path_value: str | None) -> str | None:
    """
    .env에서 받은 폰트 경로가 상대경로이면 프로젝트 루트 기준으로 변환합니다.
    """
    if not path_value:
        return None

    path = Path(path_value)

    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if path.exists():
        return str(path)

    return None


def find_font_for_country(target_country: str) -> str | None:
    """
    국가별로 적절한 폰트를 찾습니다.

    캄보디아어/미얀마어는 Arial, Malgun으로는 네모 깨짐이 발생할 수 있으므로
    Noto Sans Khmer / Noto Sans Myanmar를 우선 사용합니다.
    """
    country_key = normalize_country_key(target_country)

    font_candidates = {
        "cambodia": [
            os.getenv("FONT_CAMBODIA_PATH"),
            "fonts/NotoSansKhmer-Regular.ttf",
            "fonts/NotoSansKhmer.ttf",
            "C:/Windows/Fonts/KhmerUI.ttf",
            "C:/Windows/Fonts/khmerui.ttf",
        ],
        "myanmar": [
            os.getenv("FONT_MYANMAR_PATH"),
            "fonts/NotoSansMyanmar-Regular.ttf",
            "fonts/NotoSansMyanmar.ttf",
            "C:/Windows/Fonts/mmrtext.ttf",
            "C:/Windows/Fonts/MMRTEXT.TTF",
            "C:/Windows/Fonts/mmrtextb.ttf",
            "C:/Windows/Fonts/MMRTEXTB.TTF",
        ],
        "vietnam": [
            os.getenv("FONT_VIETNAM_PATH"),
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        ],
        "default": [
            os.getenv("FONT_DEFAULT_PATH"),
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/malgun.ttf",
        ],
    }

    candidates = font_candidates.get(country_key, font_candidates["default"])

    for candidate in candidates:
        resolved = resolve_font_path(candidate)

        if resolved:
            return resolved

    return None


def is_valid_ttf_like_file(font_path: str) -> tuple[bool, str]:
    """
    ReportLab TTFont에 넣기 전에 실제 TTF/TTC 파일인지 간단히 검사합니다.
    """
    path = Path(font_path)

    if not path.exists():
        return False, "파일이 존재하지 않습니다."

    if path.stat().st_size < 1024:
        return False, "파일 크기가 너무 작습니다. 잘못 다운로드된 파일일 수 있습니다."

    with open(path, "rb") as f:
        header = f.read(16)

    if header.startswith(b"<!DOCTYPE") or header.startswith(b"<html"):
        return False, "HTML 페이지가 저장된 파일입니다. Raw TTF 파일을 다시 다운로드하세요."

    if header.startswith(b"wOF2") or header.startswith(b"wOFF"):
        return False, "WOFF/WOFF2 웹폰트입니다. ReportLab에는 TTF 파일이 필요합니다."

    if header[:4] in [b"\x00\x01\x00\x00", b"true", b"ttcf"]:
        return True, "TTF/TTC 파일로 보입니다."

    if header.startswith(b"OTTO"):
        return False, "OTF 파일입니다. ReportLab TTFont에서 실패할 수 있으니 TTF 파일을 사용하세요."

    return False, f"알 수 없는 폰트 형식입니다. header={header!r}"


def register_font(target_country: str) -> str:
    """
    ReportLab에 국가별 폰트를 등록하고 font_name을 반환합니다.

    중요:
    국가별로 다른 font_name을 사용해야 합니다.
    같은 이름을 재사용하면 이전에 등록된 Arial/Malgun 폰트가 계속 사용되어
    캄보디아어/미얀마어가 네모로 깨질 수 있습니다.
    """
    country_key = normalize_country_key(target_country)
    font_path = find_font_for_country(target_country)

    if not font_path:
        if country_key == "cambodia":
            raise FileNotFoundError(
                "캄보디아어 PDF 생성을 위한 폰트를 찾지 못했습니다.\n"
                "아래 중 하나를 설정하세요.\n"
                "1. fonts/NotoSansKhmer-Regular.ttf 파일 추가\n"
                "2. .env에 FONT_CAMBODIA_PATH=폰트경로 설정"
            )

        if country_key == "myanmar":
            raise FileNotFoundError(
                "미얀마어 PDF 생성을 위한 폰트를 찾지 못했습니다.\n"
                "아래 중 하나를 설정하세요.\n"
                "1. fonts/NotoSansMyanmar-Regular.ttf 파일 추가\n"
                "2. .env에 FONT_MYANMAR_PATH=폰트경로 설정"
            )

        return "Helvetica"

    is_valid, reason = is_valid_ttf_like_file(font_path)

    if not is_valid:
        raise ValueError(
            f"폰트 파일 형식이 올바르지 않습니다.\n"
            f"target_country={target_country}\n"
            f"country_key={country_key}\n"
            f"font_path={font_path}\n"
            f"reason={reason}\n\n"
            f"해결 방법:\n"
            f"1. 해당 파일을 삭제하세요.\n"
            f"2. Google Fonts에서 실제 TTF 파일을 다시 다운로드하세요.\n"
            f"3. fonts 폴더에 NotoSansKhmer-Regular.ttf 또는 "
            f"NotoSansMyanmar-Regular.ttf 이름으로 넣으세요."
        )

    safe_name = Path(font_path).stem.replace("-", "_").replace(" ", "_")
    font_name = f"MarketBridge_{country_key}_{safe_name}"

    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            TTFont(
                font_name,
                font_path,
            )
        )

    print(f"[PDF FONT] target_country={target_country}")
    print(f"[PDF FONT] country_key={country_key}")
    print(f"[PDF FONT] font_path={font_path}")
    print(f"[PDF FONT] font_name={font_name}")

    return font_name


def escape_text(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def truncate(text: str, max_chars: int | None) -> str:
    text = str(text or "").strip()

    if max_chars is None:
        return text

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 1].rstrip() + "…"


def make_p(
    text: str,
    style: ParagraphStyle,
    max_chars: int | None = None,
) -> Paragraph:
    return Paragraph(
        escape_text(truncate(text, max_chars)),
        style,
    )


def is_compact(report: TranslatedUniversalDocument) -> bool:
    return report.layout_style in ["compact_form_report", "table_heavy_report"]


def make_styles(font_name: str, compact: bool) -> dict:
    base = getSampleStyleSheet()

    if compact:
        return {
            "header": ParagraphStyle(
                "Header",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7,
                leading=9,
                alignment=2,
            ),
            "title": ParagraphStyle(
                "Title",
                parent=base["Title"],
                fontName=font_name,
                fontSize=16,
                leading=20,
                alignment=1,
                spaceAfter=8,
            ),
            "section": ParagraphStyle(
                "Section",
                parent=base["Heading2"],
                fontName=font_name,
                fontSize=10.5,
                leading=13,
                spaceBefore=6,
                spaceAfter=2,
            ),
            "body": ParagraphStyle(
                "Body",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7.4,
                leading=9.4,
                spaceAfter=2,
            ),
            "cell": ParagraphStyle(
                "Cell",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7,
                leading=9,
            ),
            "cell_small": ParagraphStyle(
                "CellSmall",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=6.5,
                leading=8,
            ),
            "label": ParagraphStyle(
                "Label",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7,
                leading=9,
                alignment=1,
            ),
            "bullet": ParagraphStyle(
                "Bullet",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7.2,
                leading=9,
                leftIndent=7,
                firstLineIndent=-5,
                spaceAfter=1,
            ),
            "note": ParagraphStyle(
                "Note",
                parent=base["BodyText"],
                fontName=font_name,
                fontSize=7,
                leading=9,
            ),
        }

    return {
        "header": ParagraphStyle(
            "Header",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            alignment=2,
        ),
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName=font_name,
            fontSize=18,
            leading=24,
            alignment=1,
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=15,
            spaceAfter=5,
        ),
        "cell": ParagraphStyle(
            "Cell",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=12,
        ),
        "cell_small": ParagraphStyle(
            "CellSmall",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=10,
        ),
        "label": ParagraphStyle(
            "Label",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            alignment=1,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9.5,
            leading=13,
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=2,
        ),
        "note": ParagraphStyle(
            "Note",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#333333"),
        ),
    }


def make_table(
    rows: list[list[str]],
    styles: dict,
    font_name: str,
    total_width_mm: float,
    compact: bool,
    header_row: bool = False,
    label_columns: list[int] | None = None,
) -> Table:
    if not rows:
        rows = [[""]]

    max_cols = max(len(row) for row in rows)
    normalized_rows = []

    for row in rows:
        padded = row + [""] * (max_cols - len(row))
        normalized_rows.append(padded)

    style_for_cell = styles["cell_small"] if compact else styles["cell"]

    table_data = [
        [
            make_p(
                cell,
                style_for_cell,
                260 if not compact else 140,
            )
            for cell in row
        ]
        for row in normalized_rows
    ]

    total_width = total_width_mm * mm
    col_widths = [total_width / max_cols] * max_cols

    table = Table(
        table_data,
        colWidths=col_widths,
    )

    commands = [
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3 if compact else 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 if compact else 5),
    ]

    if header_row:
        commands.append(
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEDED"))
        )

    if label_columns:
        for col in label_columns:
            if col < max_cols:
                commands.append(
                    ("BACKGROUND", (col, 0), (col, -1), colors.HexColor("#EDEDED"))
                )

    table.setStyle(TableStyle(commands))

    return table


def render_block(
    block: UniversalBlock,
    story: list,
    styles: dict,
    font_name: str,
    compact: bool,
):
    width = 180

    if block.type == "header_text":
        if block.text:
            story.append(make_p(block.text, styles["header"], 80))
            story.append(Spacer(1, 3 if compact else 5))

    elif block.type == "title":
        text = block.text or block.title
        if text:
            story.append(make_p(text, styles["title"], 100))
            story.append(Spacer(1, 4 if compact else 8))

    elif block.type == "subtitle":
        text = block.text or block.title
        if text:
            story.append(make_p(text, styles["section"], 120))

    elif block.type == "meta_table":
        if block.rows:
            story.append(
                make_table(
                    rows=block.rows,
                    styles=styles,
                    font_name=font_name,
                    total_width_mm=width,
                    compact=compact,
                    header_row=False,
                    label_columns=[0, 2, 4],
                )
            )
            story.append(Spacer(1, 6 if compact else 10))

    elif block.type == "summary_table":
        if block.rows:
            story.append(
                make_table(
                    rows=block.rows,
                    styles=styles,
                    font_name=font_name,
                    total_width_mm=width,
                    compact=compact,
                    header_row=False,
                    label_columns=[0],
                )
            )
            story.append(Spacer(1, 6 if compact else 10))

    elif block.type == "section":
        title = block.title or block.text
        if title:
            story.append(make_p(title, styles["section"], 90))
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.8,
                    color=colors.black,
                    spaceBefore=0,
                    spaceAfter=3 if compact else 6,
                )
            )

    elif block.type == "paragraph":
        if block.text:
            story.append(
                make_p(
                    block.text,
                    styles["body"],
                    600 if not compact else 430,
                )
            )

    elif block.type == "bullet_list":
        for item in block.items:
            story.append(
                make_p(
                    "• " + item,
                    styles["bullet"],
                    250 if not compact else 170,
                )
            )

    elif block.type == "table":
        if block.title:
            story.append(make_p(block.title, styles["section"], 90))

        if block.rows:
            story.append(
                make_table(
                    rows=block.rows,
                    styles=styles,
                    font_name=font_name,
                    total_width_mm=width,
                    compact=compact,
                    header_row=True,
                )
            )
            story.append(Spacer(1, 5 if compact else 9))

    elif block.type == "note":
        rows = [["Note", block.text or ""]]

        if block.rows:
            rows = block.rows

        story.append(
            make_table(
                rows=rows,
                styles=styles,
                font_name=font_name,
                total_width_mm=width,
                compact=compact,
                header_row=False,
                label_columns=[0],
            )
        )
        story.append(Spacer(1, 4))

    elif block.type == "divider":
        story.append(
            HRFlowable(
                width="100%",
                thickness=0.8,
                color=colors.black,
                spaceBefore=2,
                spaceAfter=4,
            )
        )


def make_universal_report_pdf(
    document: TranslatedUniversalDocument,
    original_filename: str = "",
) -> bytes:
    buffer = BytesIO()

    compact = is_compact(document)
    font_name = register_font(document.target_country)
    styles = make_styles(font_name, compact)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=(14 if compact else 18) * mm,
        leftMargin=(14 if compact else 18) * mm,
        topMargin=(12 if compact else 18) * mm,
        bottomMargin=(12 if compact else 18) * mm,
    )

    story = []

    has_title_block = any(block.type == "title" for block in document.blocks)

    if not has_title_block:
        story.append(make_p(document.title, styles["title"], 100))

    sorted_blocks = sorted(document.blocks, key=lambda b: b.order)

    for block in sorted_blocks:
        render_block(
            block=block,
            story=story,
            styles=styles,
            font_name=font_name,
            compact=compact,
        )

    doc.build(story)

    buffer.seek(0)
    return buffer.read()