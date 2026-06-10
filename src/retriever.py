import pandas as pd


class SimpleCSVRetriever:
    """
    CSV 데이터를 기반으로 사용자의 입력 문장에서 관련 용어를 찾는 간단한 검색기입니다.
    나중에 FAISS/Chroma RAG로 바꾸기 전 MVP용으로 사용합니다.
    """

    def __init__(self, data: dict[str, pd.DataFrame]):
        self.data = data

    def _contains(self, text: str, keyword: str) -> bool:
        if not keyword or not isinstance(keyword, str):
            return False

        return keyword.strip().lower() in text.lower()

    def search_by_column(
        self,
        df: pd.DataFrame,
        text: str,
        keyword_col: str,
        max_rows: int = 10,
    ) -> pd.DataFrame:
        if df.empty or keyword_col not in df.columns:
            return pd.DataFrame()

        matched_rows = []

        for _, row in df.iterrows():
            keyword = str(row.get(keyword_col, "")).strip()

            if self._contains(text, keyword):
                matched_rows.append(row)

        if not matched_rows:
            return pd.DataFrame()

        return pd.DataFrame(matched_rows).head(max_rows)

    def search_marketing_terms(self, text: str) -> pd.DataFrame:
        return self.search_by_column(
            self.data.get("marketing_terms", pd.DataFrame()),
            text,
            "term_ko",
        )

    def search_slang_terms(self, text: str) -> pd.DataFrame:
        return self.search_by_column(
            self.data.get("slang_terms", pd.DataFrame()),
            text,
            "expression",
        )

    def search_finance_terms(self, text: str) -> pd.DataFrame:
        return self.search_by_column(
            self.data.get("finance_terms", pd.DataFrame()),
            text,
            "term_ko",
        )

    def search_risk_expressions(self, text: str) -> pd.DataFrame:
        return self.search_by_column(
            self.data.get("risk_expressions", pd.DataFrame()),
            text,
            "expression",
        )

    def dataframe_to_context(self, df: pd.DataFrame, title: str) -> str:
        if df.empty:
            return f"[{title}]\n관련 항목 없음\n"

        lines = [f"[{title}]"]

        for idx, row in df.iterrows():
            row_text = []
            for col in df.columns:
                value = str(row.get(col, "")).strip()
                if value and value.lower() != "nan":
                    row_text.append(f"{col}: {value}")

            lines.append("- " + " / ".join(row_text))

        return "\n".join(lines)

    def build_context(self, text: str) -> dict[str, str]:
        marketing_df = self.search_marketing_terms(text)
        slang_df = self.search_slang_terms(text)
        finance_df = self.search_finance_terms(text)
        risk_df = self.search_risk_expressions(text)

        return {
            "marketing_terms": self.dataframe_to_context(
                marketing_df,
                "감지된 마케팅 용어"
            ),
            "slang_terms": self.dataframe_to_context(
                slang_df,
                "감지된 밈/은어/트렌드 표현"
            ),
            "finance_terms": self.dataframe_to_context(
                finance_df,
                "감지된 금융 용어"
            ),
            "risk_expressions": self.dataframe_to_context(
                risk_df,
                "감지된 위험 표현"
            ),
            "has_risk_expression": not risk_df.empty,
        }