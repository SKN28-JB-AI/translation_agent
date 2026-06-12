from pathlib import Path
import pandas as pd
from core.config import DATA_DIR


def _contains(text: str, keyword: str) -> bool:
    return bool(keyword) and keyword.lower() in text.lower()


def _scan_csv(path: Path, keyword_col: str, text: str, title: str) -> str:
    if not path.exists():
        return f"[{title}]\n파일 없음: {path}\n"

    df = pd.read_csv(path)

    if keyword_col not in df.columns:
        return f"[{title}]\n검색 컬럼 없음: {keyword_col}\n"

    lines = [f"[{title}]"]
    matched = 0

    for _, row in df.iterrows():
        keyword = str(row.get(keyword_col, "")).strip()

        if _contains(text, keyword):
            matched += 1
            row_items = []

            for col, value in row.items():
                if pd.notna(value) and str(value).strip():
                    row_items.append(f"{col}: {value}")

            lines.append("- " + " / ".join(row_items))

    if matched == 0:
        lines.append("관련 항목 없음")

    return "\n".join(lines)


def build_exact_match_context(text: str) -> str:
    sections = [
        _scan_csv(
            DATA_DIR / "glossary" / "marketing_terms.csv",
            "term_ko",
            text,
            "정확 매칭: 마케팅 용어",
        ),
        _scan_csv(
            DATA_DIR / "glossary" / "slang_terms.csv",
            "expression",
            text,
            "정확 매칭: 밈/은어",
        ),
        _scan_csv(
            DATA_DIR / "glossary" / "finance_terms.csv",
            "term_ko",
            text,
            "정확 매칭: 금융 용어",
        ),
        _scan_csv(
            DATA_DIR / "rules" / "risk_expressions.csv",
            "expression",
            text,
            "정확 매칭: 위험 표현",
        ),
    ]

    return "\n\n".join(sections)