"""
World Bank Open Data API에서 국가별 지표를 가져와 RAG용 JSONL로 변환합니다.

이 스크립트는 DataReportal/TikTok/Google Trends 원문 크롤링을 하지 않습니다.
비교적 사용 조건이 명확한 World Bank API만 사용합니다.
"""

from pathlib import Path
import json
import time
import requests

OUT_DIR = Path("data/external/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "worldbank_country_indicators.jsonl"

COUNTRIES = {
    "vietnam": "VNM",
    "cambodia": "KHM",
    "myanmar": "MMR",
}

INDICATORS = {
    "IT.NET.USER.ZS": "Individuals using the Internet (% of population)",
    "IT.CEL.SETS.P2": "Mobile cellular subscriptions (per 100 people)",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    "SP.POP.TOTL": "Population, total",
    "FX.OWN.TOTL.ZS": "Account ownership at a financial institution or with a mobile-money-service provider (% of population ages 15+)",
}


def fetch_indicator(country_code: str, indicator: str):
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    params = {
        "format": "json",
        "per_page": 100,
        "mrv": 10,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        return []

    return data[1]


def build_summary(country_key: str, country_code: str, indicator_code: str, rows: list[dict]) -> str:
    indicator_name = INDICATORS[indicator_code]

    valid_rows = [row for row in rows if row.get("value") is not None]
    if not valid_rows:
        return (
            f"국가: {country_key}\n"
            f"지표: {indicator_name}\n"
            f"최근 World Bank API 응답에서 유효한 값이 없습니다.\n"
            f"마케팅 기획서 번역에서는 이 지표를 확정 근거로 사용하지 마세요."
        )

    latest = valid_rows[0]
    year = latest.get("date")
    value = latest.get("value")

    return (
        f"국가: {country_key}\n"
        f"World Bank 국가 코드: {country_code}\n"
        f"지표: {indicator_name}\n"
        f"지표 코드: {indicator_code}\n"
        f"최근 값: {value} ({year})\n"
        f"활용 방향: 광고/마케팅 기획서 번역 시 현지 디지털 접근성, 모바일 환경, 금융 접근성에 대한 "
        f"일반적 배경 설명으로만 사용하세요. 과도한 시장 판단이나 최신 SNS 트렌드 근거로 단정하지 마세요."
    )


def main():
    count = 0
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for country_key, country_code in COUNTRIES.items():
            for indicator_code in INDICATORS:
                try:
                    rows = fetch_indicator(country_code, indicator_code)
                    page_content = build_summary(country_key, country_code, indicator_code, rows)

                    doc = {
                        "page_content": page_content,
                        "metadata": {
                            "source_type": "worldbank_indicator",
                            "source_name": "World Bank Open Data API",
                            "country": country_key,
                            "country_code": country_code,
                            "indicator_code": indicator_code,
                            "indicator_name": INDICATORS[indicator_code],
                            "license_note": "Check World Bank Open Data Terms. Cite World Bank as source.",
                        },
                    }

                    f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                    count += 1
                    time.sleep(0.2)

                except Exception as e:
                    print(f"[WARN] failed {country_key}/{indicator_code}: {e}")

    print(f"saved: {OUT_PATH} / docs: {count}")


if __name__ == "__main__":
    main()