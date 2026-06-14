# MarketBridge-AI FastAPI 기능 정리 노트

## 1. 프로젝트 개요

**MarketBridge-AI**는 은행권·금융권 마케팅 문서를 동남아 국가 언어로 번역하고, 문서 구조를 유지한 상태로 결과를 제공하는 **LLM 기반 AI 번역 Agent 프로토타입**이다.

이 프로젝트는 단순 문장 번역기가 아니라, PDF 보고서를 업로드하면 문서의 제목, 표, 문단, 목록 구조를 분석하고 대상 국가 언어로 번역한 뒤 JSON 또는 PDF 형태로 활용할 수 있도록 설계되었다.

현재 기준 대상 국가는 다음과 같다.

| 국가 코드 | 대상 국가 | 대상 언어 |
|---|---|---|
| `vietnam` | 베트남 | 베트남어 |
| `cambodia` | 캄보디아 | 크메르어 |
| `myanmar` | 미얀마 | 미얀마어 |

---

## 2. 전체 작동 흐름

FastAPI 기준 전체 흐름은 다음과 같다.

```text
사용자 / Swagger UI / 프론트엔드
→ FastAPI 엔드포인트 호출
→ PDF 또는 텍스트 입력 수신
→ PDF인 경우 텍스트 추출
→ LLM 기반 문서 구조 분석
→ 대상 국가 언어로 번역
→ JSON 결과 반환
→ 필요 시 PDF 재생성 또는 번역 검수
```

코드 구조 기준으로 보면 다음과 같다.

```text
api_main.py
→ FastAPI 엔드포인트 담당

documents/pdf_utils.py
→ PDF 텍스트 추출 및 품질 확인

agents/agent.py
→ 일반 텍스트 번역 담당

agents/universal_document_pipeline.py
→ PDF 문서 구조 분석, 번역, 검수 담당

documents/universal_pdf_renderer.py
→ 번역 결과를 PDF로 재생성

core/prompts.py
→ 프롬프트 관리

models/
→ 요청/응답 데이터 구조 관리
```

---

## 3. 실행 방법

프로젝트 루트 경로로 이동한다.

```powershell
cd C:\Users\test\OneDrive\Desktop\translation_agent
```

가상환경을 활성화한다.

```powershell
conda activate jb_project
```

FastAPI 서버를 실행한다.

```powershell
python -m uvicorn api_main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

실행 후 Swagger 문서 페이지에 접속한다.

```text
http://localhost:8000/docs
```

서버 상태 확인 주소는 다음과 같다.

```text
http://localhost:8000/health
```

주의할 점은 브라우저에서 `0.0.0.0`으로 접속하는 것이 아니라 `localhost`로 접속해야 한다는 점이다.

---

## 4. 주요 API 기능

### 4.1 서버 상태 확인 API

```http
GET /health
```

서버가 정상적으로 실행 중인지 확인하는 API이다.

예상 응답:

```json
{
  "status": "ok"
}
```

이 API는 발표나 테스트 시 가장 먼저 서버 동작 여부를 확인하는 용도로 사용할 수 있다.

---

### 4.2 텍스트 번역 API

```http
POST /api/text/translate
```

일반 텍스트를 대상 국가 언어로 번역하는 API이다.

텍스트 번역은 두 가지 방식으로 나뉜다.

| task_type | 설명 |
|---|---|
| `simple_translation` | 짧은 문장이나 일반 문장을 단순 번역 |
| `document_translation` | 문서성 텍스트를 번역하고 용어 매칭 및 RAG 참고자료 활용 |

요청 예시:

```json
{
  "text": "안녕하세요",
  "target_country": "vietnam",
  "output_style": "기획서 문체",
  "task_type": "simple_translation"
}
```

응답 예시:

```json
{
  "target_country_ko": "베트남",
  "target_language_ko": "베트남어",
  "result_markdown": "Xin chào."
}
```

`simple_translation`은 분석이나 현지화 메모 없이 번역문만 간단하게 반환한다.

반면 `document_translation`은 마케팅 문서나 금융 문서처럼 문서성 텍스트를 다룰 때 사용한다.

요청 예시:

```json
{
  "text": "신규 고객을 대상으로 모바일 금융 서비스 혜택을 소개하는 캠페인을 기획한다.",
  "target_country": "vietnam",
  "output_style": "기획서 문체",
  "task_type": "document_translation"
}
```

이 경우 내부적으로 다음 작업이 수행된다.

```text
문서성 텍스트 입력
→ 정확 매칭 용어 검색
→ RAG 참고자료 검색
→ LLM 번역
→ result_markdown 반환
```

---

### 4.3 PDF 보고서 번역 API

```http
POST /api/report/translate
```

현재 프로젝트의 핵심 기능이다.

PDF 파일을 업로드하면 다음 절차로 작동한다.

```text
PDF 업로드
→ PDF 텍스트 추출
→ 텍스트 품질 확인
→ 문서 구조 분석
→ 대상 국가 언어로 번역
→ 구조화된 JSON 반환
```

Swagger에서 입력하는 주요 값은 다음과 같다.

| 입력값 | 설명 |
|---|---|
| `file` | 번역할 PDF 파일 |
| `target_country` | `vietnam`, `cambodia`, `myanmar` 중 하나 |
| `output_style` | 번역 문체. 예: 공식 보고서 문체, 기획서 문체 |

응답 구조는 대략 다음과 같다.

```json
{
  "message": "번역 완료",
  "text_quality_ok": true,
  "text_quality_message": "보고서형 PDF 텍스트 추출 성공",
  "original_filename": "example.pdf",
  "original_text": "...",
  "parsed_document": {
    "document_type": "기획서",
    "layout_style": "general_report",
    "title": "...",
    "blocks": []
  },
  "translated_document": {
    "target_country": "베트남",
    "target_language": "베트남어",
    "document_type": "기획서",
    "layout_style": "general_report",
    "title": "...",
    "blocks": []
  }
}
```

#### 주요 응답 필드 설명

| 필드 | 설명 |
|---|---|
| `message` | 처리 결과 메시지 |
| `text_quality_ok` | PDF 텍스트 추출 품질 여부 |
| `text_quality_message` | 추출 품질 설명 |
| `original_filename` | 업로드한 원본 파일명 |
| `original_text` | PDF에서 추출한 원문 텍스트 |
| `parsed_document` | 원문을 구조화한 결과 |
| `translated_document` | 대상 언어로 번역된 구조화 문서 |

---

## 5. 문서 구조 분석 방식

PDF를 단순 문자열로 번역하지 않고, 먼저 문서 구조를 분석한다.

예를 들어 원문 PDF는 다음과 같은 블록으로 나뉜다.

```text
제목
헤더
섹션
문단
표
목록
참고자료
페이지 구분
```

구조화 결과는 `blocks` 배열 안에 저장된다.

예시:

```json
{
  "type": "section",
  "title": "Ⅳ. 콘텐츠 아이템 상세",
  "text": "",
  "rows": [],
  "items": [],
  "level": 1,
  "order": 11
}
```

표는 다음과 같은 구조로 저장된다.

```json
{
  "type": "table",
  "title": "콘텐츠 아이템 목록",
  "rows": [
    ["No.", "콘텐츠명", "구성/연출", "훅 문구 예시"],
    ["1", "처음 온 사람 표정 변화", "...", "..."]
  ],
  "items": [],
  "level": 2,
  "order": 12
}
```

이렇게 구조화하는 이유는 번역 후에도 표, 제목, 문단의 형태를 최대한 유지하기 위해서이다.

---

## 6. 번역 결과 활용 방식

`/api/report/translate`의 결과 중 가장 중요한 값은 `translated_document`이다.

이 값은 번역된 문서의 구조화 JSON이다.

활용 방식은 다음과 같다.

```text
translated_document
→ 화면에 번역 결과 표시
→ PDF 생성 API에 전달
→ 번역 검수 API에 전달
→ 추후 DB 저장 가능
```

즉, `translated_document`는 단순 결과 텍스트가 아니라 후속 기능의 입력값으로도 사용할 수 있는 핵심 데이터이다.

---

## 7. PDF 생성 API

```http
POST /api/pdf/generate
```

번역된 문서 JSON을 다시 PDF 파일로 생성하는 API이다.

입력값은 다음과 같은 구조를 가진다.

```json
{
  "original_filename": "translated_report.pdf",
  "translated_document": {
    "target_country": "베트남",
    "target_language": "베트남어",
    "document_type": "기획서",
    "layout_style": "general_report",
    "title": "...",
    "blocks": []
  }
}
```

작동 흐름은 다음과 같다.

```text
translated_document JSON 입력
→ universal_pdf_renderer.py 실행
→ 대상 언어 폰트 적용
→ 번역 PDF 생성
→ PDF 파일 응답
```

이 기능을 사용하면 번역 결과를 JSON으로만 보는 것이 아니라 실제 보고서형 PDF 파일로 다운로드할 수 있다.

---

## 8. 번역 검수 API

```http
POST /api/report/review
```

번역 결과를 검수하는 API이다.

입력값은 다음과 같다.

| 입력값 | 설명 |
|---|---|
| `original_text` | 원문 텍스트 |
| `target_country` | 대상 국가 |
| `translated_document` | 번역된 문서 JSON |

작동 흐름은 다음과 같다.

```text
원문 텍스트
+ 번역된 문서 JSON
→ LLM 기반 번역 검수
→ 오역, 누락, 문체, 용어, 형식, 위험 표현 확인
```

특히 은행/금융 문서에서는 다음과 같은 표현이 문제가 될 수 있다.

```text
수익 보장
원금 보장
무조건 혜택
확정 수익
손실 없음
최고 금리
```

검수 기능은 이런 표현이 번역 과정에서 과장되거나 보장처럼 들리지 않는지 확인하는 데 활용된다.

---

## 9. 현재 프로젝트에서 사용하는 외부 API

현재 프로젝트는 Papago, Google Translate, DeepL 같은 번역 전용 API를 사용하는 구조가 아니다.

현재 구조는 다음과 같다.

```text
FastAPI
→ 내부 Python 파이프라인 실행
→ ChatOpenAI 기반 LLM API 호출
→ 문서 분석, 번역, 검수 수행
```

즉, 실제 번역은 OpenAI-compatible LLM API를 통해 수행된다.

`.env`에서 다음 설정을 통해 사용할 모델과 API 주소를 관리한다.

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

OpenRouter를 사용하는 경우 예시는 다음과 같다.

```env
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-oss-120b:free
```

---

## 10. FastAPI와 Streamlit의 관계

현재 구조에서 FastAPI와 Streamlit은 역할이 다르다.

```text
FastAPI
→ 외부에서 호출 가능한 API 서버

Streamlit
→ 데모용 사용자 화면

공통 파이프라인
→ 두 인터페이스가 함께 사용하는 내부 기능
```

현재 Streamlit이 FastAPI를 HTTP로 호출하는 구조는 아닐 수 있다.

즉, Streamlit은 다음처럼 작동할 수 있다.

```text
Streamlit 버튼 클릭
→ 내부 Python 함수 직접 호출
→ 번역 결과 표시
```

반면 FastAPI는 다음처럼 작동한다.

```text
Swagger 또는 외부 클라이언트 요청
→ HTTP API 호출
→ 내부 Python 함수 실행
→ JSON 응답 반환
```

이 구조는 잘못된 것이 아니다. 데모 UI와 API 서버가 같은 내부 로직을 공유하는 구조라고 설명할 수 있다.

---

## 11. 발표용 설명

발표에서는 다음과 같이 설명할 수 있다.

```text
MarketBridge-AI는 은행권 마케팅 문서의 동남아 현지화를 지원하는 FastAPI 기반 AI 번역 Agent입니다.

사용자가 PDF 보고서를 업로드하면 서버는 PDF 텍스트를 추출하고,
LLM을 이용해 문서를 제목, 표, 문단, 목록 단위로 구조화합니다.

이후 대상 국가에 맞는 언어로 각 블록을 번역하고,
번역된 문서 구조를 JSON으로 반환합니다.

또한 번역 결과를 PDF로 재생성하거나,
역번역 기반 검수를 통해 오역, 누락, 문체, 금융 위험 표현을 확인할 수 있습니다.

본 프로젝트는 Papago나 Google Translate 같은 단순 번역 API가 아니라,
OpenAI-compatible LLM API를 활용해 문서 구조 분석과 번역, 검수까지 수행하는 프로토타입입니다.
```

---

## 12. 현재 구현 완료로 말할 수 있는 기능

현재 기준으로 구현 완료 또는 구현된 구조로 설명할 수 있는 기능은 다음과 같다.

```text
FastAPI 서버 구축
Swagger 기반 API 테스트
텍스트 번역 API
PDF 업로드 기반 보고서 번역 API
PDF 텍스트 추출
문서 구조 분석
대상 국가별 언어 번역
번역 결과 JSON 반환
번역 결과 PDF 재생성
번역 검수 구조
OpenAI-compatible LLM API 연동
```

---

## 13. 아직 조심해서 말해야 하는 부분

다음 표현은 발표나 보고서에서 조심하는 것이 좋다.

```text
은행 기업에 바로 실서비스 적용 가능
금융 규제 검토 완전 자동화
전문 번역가 수준 품질 보장
자체 번역 모델 학습 완료
```

현재 프로젝트는 모델을 직접 학습시킨 것이 아니라, 기존 LLM API와 문서 처리 파이프라인을 결합한 프로토타입이다.

따라서 정확한 표현은 다음과 같다.

```text
은행권 마케팅 문서 번역을 지원하는 LLM 기반 AI Agent 프로토타입
```

---

## 14. 향후 개선 방향

실제 은행 기업 환경에서 활용하려면 다음 기능을 추가하면 좋다.

```text
금융 용어 표준 사전 강화
국가별 규제 표현 필터 추가
개인정보 및 민감정보 마스킹
번역 품질 정량 평가
사람 검수 승인 프로세스
API 호출 로그 및 감사 기록
보안 환경 배포
고성능 LLM 모델 적용
국가별 표현 스타일 가이드 추가
```

---

## 15. 한 줄 요약

**MarketBridge-AI는 은행권 마케팅 PDF 문서를 업로드하면 문서 구조를 분석하고, 대상 국가 언어로 번역한 뒤 JSON/PDF/검수 결과로 활용할 수 있게 하는 FastAPI 기반 LLM 번역 Agent 프로토타입이다.**
