from pathlib import Path
import json
import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import DATA_DIR


def csv_row_to_text(row: pd.Series) -> str:
    lines = []
    for col, value in row.items():
        if pd.notna(value) and str(value).strip():
            lines.append(f"{col}: {value}")
    return "\n".join(lines)


def load_csv_as_documents(path: Path, source_type: str) -> list[Document]:
    if not path.exists():
        print(f"[WARN] missing CSV: {path}")
        return []

    df = pd.read_csv(path)
    docs = []

    for idx, row in df.iterrows():
        page_content = csv_row_to_text(row)
        metadata = {
            "source_type": source_type,
            "source_file": str(path),
            "row_id": idx,
            "country": "all",
        }
        docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


def load_jsonl_documents(path: Path) -> list[Document]:
    if not path.exists():
        print(f"[WARN] missing JSONL: {path}")
        return []

    docs = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            item = json.loads(line)
            page_content = item.get("page_content") or item.get("text") or ""
            metadata = item.get("metadata", {})

            docs.append(Document(page_content=page_content, metadata=metadata))

    return docs


def load_markdown_documents(folder: Path) -> list[Document]:
    docs = []

    if not folder.exists():
        return docs

    for path in folder.glob("*.md"):
        text = path.read_text(encoding="utf-8")

        docs.append(
            Document(
                page_content=text,
                metadata={
                    "source_type": "manual_note",
                    "source_file": str(path),
                    "country": "all",
                    "license_note": "User-created summary note. Do not paste copyrighted original text.",
                },
            )
        )

    return docs


def build_all_documents() -> list[Document]:
    docs = []

    docs += load_csv_as_documents(
        DATA_DIR / "glossary" / "marketing_terms.csv",
        "marketing_terms",
    )
    docs += load_csv_as_documents(
        DATA_DIR / "glossary" / "slang_terms.csv",
        "slang_terms",
    )
    docs += load_csv_as_documents(
        DATA_DIR / "glossary" / "finance_terms.csv",
        "finance_terms",
    )
    docs += load_csv_as_documents(
        DATA_DIR / "rules" / "risk_expressions.csv",
        "risk_expressions",
    )

    docs += load_jsonl_documents(
        DATA_DIR / "external" / "processed" / "worldbank_country_indicators.jsonl"
    )

    docs += load_markdown_documents(
        DATA_DIR / "external" / "manual_notes"
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=120,
    )

    split_docs = splitter.split_documents(docs)

    print(f"loaded docs: {len(docs)} / split docs: {len(split_docs)}")

    return split_docs