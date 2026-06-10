import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    openai_api_key: str
    openai_base_url: str
    openai_model: str


def get_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY가 설정되지 않았습니다. "
            ".env 파일을 만들고 OPENAI_API_KEY를 입력하세요."
        )

    return Settings(
        openai_api_key=api_key,
        openai_base_url=base_url,
        openai_model=model,
    )