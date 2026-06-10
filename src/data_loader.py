from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_csv(relative_path: str) -> pd.DataFrame:
    path = DATA_DIR / relative_path

    if not path.exists():
        print(f"[WARN] CSV 파일을 찾을 수 없습니다: {path}")
        return pd.DataFrame()

    return pd.read_csv(path)


def load_all_data() -> dict[str, pd.DataFrame]:
    return {
        "marketing_terms": load_csv("glossary/marketing_terms.csv"),
        "slang_terms": load_csv("glossary/slang_terms.csv"),
        "finance_terms": load_csv("glossary/finance_terms.csv"),
        "risk_expressions": load_csv("rules/risk_expressions.csv"),
    }