from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from core.config import get_settings, VECTOR_DIR
from document_builder import build_all_documents


def main():
    settings = get_settings()
    docs = build_all_documents()

    if not docs:
        raise RuntimeError("벡터DB에 넣을 문서가 없습니다. data 폴더를 확인하세요.")

    print(f"문서 개수: {len(docs)}")
    print(f"임베딩 모델: {settings.embedding_model}")
    print(f"Base URL: {settings.openai_base_url}")
    print("API Key 로드 여부:", "로드됨" if settings.openai_api_key else "없음")

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
    )

    vectorstore = FAISS.from_documents(docs, embeddings)

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTOR_DIR))

    print(f"FAISS vectorstore saved to: {VECTOR_DIR}")


if __name__ == "__main__":
    main()