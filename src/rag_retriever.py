from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import get_settings, VECTOR_DIR


class SafeRAGRetriever:
    def __init__(self):
        settings = get_settings()

        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        if not VECTOR_DIR.exists():
            raise FileNotFoundError(
                f"벡터DB가 없습니다: {VECTOR_DIR}\n"
                "먼저 `python src/build_vector_db.py`를 실행하세요."
            )

        self.vectorstore = FAISS.load_local(
            str(VECTOR_DIR),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    def retrieve(self, query: str, target_country: str, k: int = 10) -> list[Document]:
        docs = self.vectorstore.similarity_search(
            query,
            k=max(k * 3, 20),
        )

        filtered = []
        fallback = []

        for doc in docs:
            country = doc.metadata.get("country", "all")

            if country in ["all", target_country, None, "unknown"]:
                filtered.append(doc)
            else:
                fallback.append(doc)

        selected = filtered[:k]

        if len(selected) < k:
            selected += fallback[: k - len(selected)]

        return selected


def format_docs(docs: list[Document]) -> str:
    if not docs:
        return "검색된 RAG 참고자료 없음"

    lines = []

    for idx, doc in enumerate(docs, start=1):
        metadata = doc.metadata
        source_type = metadata.get("source_type", "unknown")
        source_name = metadata.get("source_name") or metadata.get("source_file", "unknown")
        country = metadata.get("country", "all")

        lines.append(
            f"[문서 {idx}]\n"
            f"source_type: {source_type}\n"
            f"source: {source_name}\n"
            f"country: {country}\n"
            f"content:\n{doc.page_content}"
        )

    return "\n\n".join(lines)