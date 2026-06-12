import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
VECTOR_DIR = PROJECT_ROOT / "vectorstore" / "faiss_index"

ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)


@dataclass
class Settings:
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    embedding_model: str
    vision_model: str


def get_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    vision_model = os.getenv("OPENAI_VISION_MODEL", model)

    if not api_key:
        raise ValueError(
            f"OPENAI_API_KEY가 없습니다. .env 파일 위치를 확인하세요: {ENV_PATH}"
        )

    return Settings(
        openai_api_key=api_key,
        openai_base_url=base_url,
        openai_model=model,
        embedding_model=embedding_model,
        vision_model=vision_model,
    )