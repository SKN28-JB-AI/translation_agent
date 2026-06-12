# MarketBridge-AI

동남아 현지 담당자를 위한 광고·마케팅 문서 번역 및 현지화 AI Agent 서비스입니다.

한국어 광고/마케팅 기획서와 보고서 PDF를 베트남어, 크메르어, 미얀마어로 번역하고, 반대로 동남아 언어 문서를 한국어로 번역할 수 있습니다.
단순 번역뿐 아니라 문서 구조 분석, 공통 블록 기반 PDF 재생성, 번역 검수, RAG 기반 용어 참고 기능을 포함합니다.

---

## 1. 프로젝트 개요

MarketBridge-AI는 한국어 기반 마케팅 문서를 동남아 현지 담당자가 이해할 수 있는 언어와 문체로 변환하기 위한 AI Agent입니다.

기존 번역기는 문서의 맥락, 마케팅 용어, 현지 표현, 문서 구조를 충분히 반영하지 못하는 한계가 있습니다.
본 프로젝트는 다음 문제를 해결하는 것을 목표로 합니다.

* 한국어 마케팅 문서를 동남아 언어로 자연스럽게 번역
* 베트남어, 크메르어, 미얀마어 문서를 한국어로 역번역
* PDF 보고서의 제목, 표, 섹션, 목록 구조를 분석하여 재구성
* 번역 결과를 다시 한국어로 해석해 오역, 누락, 추가 내용을 검수
* 용어집과 참고 데이터를 활용한 RAG 기반 번역 보조

---

## 2. 주요 기능

### 2.1 텍스트 입력 번역

한국어 광고/마케팅 문장을 입력하면 대상 국가 언어로 번역합니다.

지원 국가:

* 베트남
* 캄보디아
* 미얀마

주요 처리 내용:

* 마케팅 문체 반영
* 현지 담당자가 이해하기 쉬운 표현으로 변환
* 위험 표현, 과장 표현 완화
* 용어집 기반 정확 매칭
* RAG 검색 근거 제공

---

### 2.2 한국어 PDF → 동남아 언어 번역

텍스트 선택이 가능한 한국어 PDF 보고서를 업로드하면 다음 흐름으로 처리합니다.

```text
PDF 업로드
→ 텍스트 추출
→ 공통 문서 블록 구조 분석
→ 대상 언어 번역
→ 번역 구조 미리보기
→ PDF 재생성
```

문서 구조는 다음과 같은 블록으로 분석됩니다.

* title
* subtitle
* header_text
* meta_table
* summary_table
* section
* paragraph
* bullet_list
* table
* note
* divider

---

### 2.3 동남아어 PDF → 한국어 번역

베트남어, 크메르어, 미얀마어 PDF를 한국어 문서로 번역합니다.

```text
동남아어 PDF 업로드
→ 텍스트 추출
→ 원문 언어 기준 문서 구조 분석
→ 한국어 번역
→ 한국어 PDF 생성
```

---

### 2.4 번역 검수

번역 결과를 다시 한국어로 해석한 뒤, 원문과 비교합니다.

검수 항목:

* 오역 여부
* 누락 내용 여부
* 원문에 없는 내용 추가 여부
* 문체 자연스러움
* 용어 번역 적절성
* 표, 섹션, 목록 구조 유지 여부
* 과장 표현 또는 위험 표현 여부

검수 결과는 다음 형태로 제공됩니다.

* 번역 품질 점수
* 전체 판단
* 역번역 요약
* 한국어 역번역문
* 문제 목록
* 수정 제안
* 최종 검수 의견
* TXT 다운로드

---

### 2.5 PDF 요약

업로드한 PDF에서 텍스트를 추출한 뒤 요약합니다.

---

### 2.6 Vision PDF 분석 보조 모드

이미지형 PDF 또는 PPT형 PDF처럼 텍스트 추출이 어려운 파일을 확인하기 위한 보조 모드입니다.

현재 메인 번역 기능은 텍스트 선택 가능한 PDF에 최적화되어 있습니다.

---

## 3. 기술 스택

### Backend / AI

* Python
* LangChain
* OpenAI-compatible Chat API
* FAISS Vector Store
* RAG Retrieval
* Pydantic Structured Output

### Web UI

* Streamlit

### API Server

* FastAPI
* Uvicorn

### PDF Processing

* pypdf
* ReportLab

### Data

* 마케팅 용어집
* 은어/현지 표현 용어집
* 금융/위험 표현 용어집
* World Bank 국가 지표 데이터
* 수동 현지화 참고 노트

---

## 4. 프로젝트 구조

```text
translation_agent/
├── data/
│   ├── glossary/
│   │   ├── marketing_terms.csv
│   │   ├── slang_terms.csv
│   │   └── finance_terms.csv
│   ├── rules/
│   │   └── risk_expressions.csv
│   └── external/
│       ├── processed/
│       │   └── worldbank_country_indicators.jsonl
│       └── manual_notes/
│           └── safe_localization_notes.md
│
├── fonts/
│   ├── NotoSansKhmer-Regular.ttf
│   └── NotoSansMyanmar-Regular.ttf
│
├── src/
│   ├── app.py
│   ├── app_pages.py
│   ├── app_services.py
│   ├── api_main.py
│   ├── api_schemas.py
│   ├── agent.py
│   ├── schemas.py
│   ├── config.py
│   ├── prompts.py
│   ├── pdf_utils.py
│   ├── file_exporter.py
│   ├── exact_matcher.py
│   ├── rag_retriever.py
│   ├── universal_document_schema.py
│   ├── universal_document_pipeline.py
│   ├── universal_pdf_renderer.py
│   ├── build_vector_db.py
│   └── collect_worldbank.py
│
├── vectorstore/
│   └── faiss_index/
│
├── .env
├── requirements.txt
└── README.md
```

---

## 5. 설치 방법

### 5.1 가상환경 생성

```bash
conda create -n jb_project python=3.12
conda activate jb_project
```

또는 venv 사용 시:

```bash
python -m venv .venv
.venv\Scripts\activate
```

---

### 5.2 패키지 설치

```bash
pip install -r requirements.txt
```

`requirements.txt` 예시:

```txt
streamlit
fastapi
uvicorn
python-multipart
python-dotenv
pydantic
langchain
langchain-openai
langchain-community
faiss-cpu
pandas
numpy
pypdf
reportlab
requests
tqdm
```

---

## 6. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```env
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

FONT_CAMBODIA_PATH=fonts/NotoSansKhmer-Regular.ttf
FONT_MYANMAR_PATH=fonts/NotoSansMyanmar-Regular.ttf
FONT_VIETNAM_PATH=C:\Windows\Fonts\arial.ttf
FONT_KOREA_PATH=C:\Windows\Fonts\malgun.ttf
FONT_DEFAULT_PATH=C:\Windows\Fonts\arial.ttf
```

OpenRouter를 사용할 경우 예시:

```env
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## 7. 폰트 설정

크메르어와 미얀마어 PDF 생성을 위해 전용 폰트가 필요합니다.

프로젝트 루트에 `fonts` 폴더를 만들고 아래 파일을 넣습니다.

```text
fonts/
├── NotoSansKhmer-Regular.ttf
└── NotoSansMyanmar-Regular.ttf
```

주의사항:

* 폰트 파일은 직접 만드는 것이 아니라 다운로드해서 사용합니다.
* GitHub 페이지를 우클릭 저장하면 HTML 파일이 `.ttf`로 저장될 수 있습니다.
* 반드시 실제 TTF 파일을 사용해야 합니다.
* 잘못된 파일을 사용하면 다음 오류가 발생할 수 있습니다.

```text
TTFError: is not a TTF file: can't read version
```

폰트 파일 확인 예시:

```python
from pathlib import Path

for path in [
    "fonts/NotoSansKhmer-Regular.ttf",
    "fonts/NotoSansMyanmar-Regular.ttf",
]:
    p = Path(path)
    print(path, p.exists(), p.stat().st_size if p.exists() else None)

    if p.exists():
        with open(p, "rb") as f:
            print(f.read(16))
```

정상 TTF 파일은 보통 다음과 같은 헤더를 가집니다.

```text
b'\x00\x01\x00\x00'
```

---

## 8. 데이터 준비

### 8.1 World Bank 데이터 수집

```bash
python src/collect_worldbank.py
```

### 8.2 Vector DB 생성

```bash
python src/build_vector_db.py
```

생성 후 다음 경로에 FAISS 인덱스가 저장됩니다.

```text
vectorstore/faiss_index/
```

---

## 9. Streamlit 실행

```bash
streamlit run src/app.py
```

실행 후 브라우저에서 Streamlit 앱이 열립니다.

주요 메뉴:

```text
텍스트 입력 번역
보고서 PDF 번역 다운로드
동남아어 PDF 한국어 번역
보고서 PDF 요약
보조: Vision PDF 분석
```

---

## 10. FastAPI 실행

프로젝트 루트에서 실행합니다.

```bash
uvicorn api_main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

API 문서 확인:

```text
http://localhost:8000/docs
```

상태 확인:

```text
http://localhost:8000/health
```

---

## 11. FastAPI 주요 엔드포인트

### 11.1 Health Check

```http
GET /health
```

응답 예시:

```json
{
  "status": "ok",
  "service": "MarketBridge-AI API"
}
```

---

### 11.2 텍스트 번역

```http
POST /api/text/translate
```

요청 예시:

```json
{
  "text": "신규 고객을 대상으로 모바일 금융 서비스의 주요 혜택을 소개한다.",
  "target_country": "vietnam",
  "output_style": "기획서 문체"
}
```

---

### 11.3 한국어 PDF → 동남아 언어 번역

```http
POST /api/report/translate
```

Form Data:

```text
file: PDF 파일
target_country: vietnam | cambodia | myanmar
output_style: 기획서 문체
```

---

### 11.4 동남아어 PDF → 한국어 번역

```http
POST /api/report/reverse-translate
```

Form Data:

```text
file: PDF 파일
source_country: vietnam | cambodia | myanmar
output_style: 업무 보고서체
```

---

### 11.5 번역 PDF 생성

```http
POST /api/report/generate-pdf
```

요청 예시:

```json
{
  "original_filename": "report.pdf",
  "translated_document": {
    "target_country": "베트남",
    "target_language": "베트남어",
    "document_type": "보고서",
    "layout_style": "compact_form_report",
    "title": "Báo cáo...",
    "summary": "...",
    "blocks": []
  }
}
```

응답:

```text
application/pdf
```

---

### 11.6 번역 검수

```http
POST /api/report/review
```

요청 예시:

```json
{
  "original_text": "한국어 원문",
  "target_country": "vietnam",
  "translated_document": {
    "target_country": "베트남",
    "target_language": "베트남어",
    "document_type": "보고서",
    "layout_style": "compact_form_report",
    "title": "Báo cáo...",
    "summary": "...",
    "blocks": []
  }
}
```

---

## 12. 실행 예시

### 12.1 Streamlit 데모 실행

```bash
streamlit run src/app.py
```

### 12.2 FastAPI 서버 실행

```bash
uvicorn api_main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

### 12.3 API 문서 접속

```text
http://localhost:8000/docs
```

---

## 13. 처리 흐름

### 한국어 → 동남아 언어 번역

```text
한국어 PDF
→ 텍스트 추출
→ 공통 문서 블록 구조 분석
→ 대상 언어 번역
→ 번역 구조 미리보기
→ PDF 생성
→ 번역 검수
```

### 동남아 언어 → 한국어 번역

```text
동남아어 PDF
→ 텍스트 추출
→ 원문 언어 기준 구조 분석
→ 한국어 번역
→ 한국어 PDF 생성
```

---

## 14. 문서 블록 구조

PDF 문서는 내부적으로 다음과 같은 공통 블록 구조로 변환됩니다.

```json
{
  "document_type": "보고서",
  "layout_style": "compact_form_report",
  "title": "문서 제목",
  "summary": "문서 요약",
  "blocks": [
    {
      "type": "title",
      "title": "",
      "text": "문서 제목",
      "rows": [],
      "items": [],
      "level": 1,
      "order": 1
    },
    {
      "type": "table",
      "title": "기대 효과",
      "text": "",
      "rows": [
        ["구분", "현재 문제", "개선 효과"]
      ],
      "items": [],
      "level": 1,
      "order": 2
    }
  ]
}
```

이 구조를 사용하면 문서 양식마다 별도 렌더러를 계속 추가하지 않고, 블록 타입에 따라 공통 PDF 렌더러가 처리할 수 있습니다.

---

## 15. 한계점

현재 시스템은 텍스트 선택이 가능한 PDF에 가장 안정적으로 동작합니다.

다음 문서는 정확도가 낮을 수 있습니다.

* 스캔 PDF
* 이미지형 PDF
* PPT를 이미지로 변환한 PDF
* 폰트 인코딩이 깨진 PDF
* 복잡한 그래픽 중심 제안서
* 원본 디자인을 픽셀 단위로 유지해야 하는 문서

PDF는 편집용 문서가 아니라 최종 출력물에 가까우므로, 원본 디자인을 완전히 보존하는 데 한계가 있습니다.

정확한 레이아웃 보존이 필요하다면 PDF보다 다음 원본 형식이 더 적합합니다.

* DOCX
* PPTX
* HWPX

---

## 16. 문제 해결

### 16.1 `ImportError: cannot import name 'MarketBridgeRAGAgent' from 'agent'`

FastAPI 실행 시 프로젝트의 `src/agent.py`가 아니라 외부 패키지의 `agent.py`를 불러온 경우입니다.

아래 명령어로 실행합니다.

```bash
uvicorn api_main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

---

### 16.2 캄보디아어 또는 미얀마어가 네모로 깨짐

전용 폰트가 없거나 잘못 등록된 경우입니다.

확인할 파일:

```text
fonts/NotoSansKhmer-Regular.ttf
fonts/NotoSansMyanmar-Regular.ttf
```

확인할 환경 변수:

```env
FONT_CAMBODIA_PATH=fonts/NotoSansKhmer-Regular.ttf
FONT_MYANMAR_PATH=fonts/NotoSansMyanmar-Regular.ttf
```

---

### 16.3 `TTFError: is not a TTF file`

폰트 파일이 실제 TTF가 아닌 경우입니다.

가능한 원인:

* HTML 페이지를 `.ttf`로 저장함
* WOFF2 파일을 `.ttf`로 이름만 바꿈
* 다운로드가 중간에 깨짐

해결 방법:

* 잘못된 폰트 파일 삭제
* 실제 TTF 파일 다시 다운로드
* `fonts/` 폴더에 다시 저장
* Streamlit 또는 FastAPI 재시작

---

### 16.4 PDF에서 텍스트가 거의 추출되지 않음

이미지형 PDF일 가능성이 큽니다.

해결 방법:

* 텍스트 선택 가능한 PDF 사용
* 원본 DOCX/PPTX/HWPX 사용
* Vision PDF 분석 보조 모드 사용

---

## 17. 향후 개선 방향

* Vision 기반 이미지형 PDF 분석 고도화
* DOCX/PPTX/HWPX 원본 문서 지원
* HTML 기반 PDF 렌더링으로 크메르어/미얀마어 조합 문자 개선
* React 프론트엔드 연결
* 사용자별 번역 이력 저장
* 문서 템플릿 선택 기능 추가
* 국가별 마케팅 표현 추천 기능 강화
* 번역 품질 평가 자동 리포트 생성

---

## 18. 실행 요약

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. World Bank 데이터 수집
python src/collect_worldbank.py

# 3. Vector DB 생성
python src/build_vector_db.py

# 4. Streamlit 실행
streamlit run src/app.py

# 5. FastAPI 실행
uvicorn api_main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
```

---

## 19. 프로젝트 핵심 요약

MarketBridge-AI는 단순 번역기가 아니라, 동남아 마케팅 문서 업무를 지원하는 문서 번역·현지화 Agent입니다.

주요 특징:

* 한국어 ↔ 동남아 언어 양방향 번역
* PDF 문서 구조 분석
* 공통 블록 기반 PDF 재생성
* 번역 검수 및 역번역
* RAG 기반 용어 참고
* Streamlit 데모와 FastAPI 백엔드 동시 제공
