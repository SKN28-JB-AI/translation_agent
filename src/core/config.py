from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# 현재 파일 위치:
# translation_agent/src/core/config.py
CORE_DIR = Path(__file__).resolve().parent
SRC_DIR = CORE_DIR.parent
PROJECT_ROOT = SRC_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"
VECTOR_DIR = VECTORSTORE_DIR / "faiss_index"
FONTS_DIR = PROJECT_ROOT / "fonts"
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    @property
    def embedding_model(self) -> str:
        return self.openai_embedding_model
    
    class Config:
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    settings = Settings()

    if not settings.openai_api_key:
        raise ValueError(
            f"OPENAI_API_KEY가 없습니다. .env 파일 위치를 확인하세요: {ENV_PATH}"
        )

    return settings

