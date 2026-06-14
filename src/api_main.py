from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models.schemas import AgentRequest
from agents.agent import MarketBridgeRAGAgent
from agents.universal_document_pipeline import (
    UniversalDocumentPipeline,
    review_result_to_text,
)
from documents.universal_pdf_renderer import make_universal_report_pdf
from documents.pdf_utils import extract_text_from_pdf_bytes, check_pdf_text_quality

from models.api_schemas import (
    TextTranslateRequest,
    TextTranslateResponse,
    ReportReviewRequest,
    PdfGenerateRequest,
)


app = FastAPI(
    title="MarketBridge-AI API",
    description="동남아 마케팅 문서 번역·현지화·검수 API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시에는 실제 프론트 주소만 넣는 게 좋음
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


agent = MarketBridgeRAGAgent()
pipeline = UniversalDocumentPipeline()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "MarketBridge-AI API",
    }


@app.post("/api/text/translate", response_model=TextTranslateResponse)
def translate_text(request: TextTranslateRequest):
    try:
        result = agent.run(
            AgentRequest(
                text=request.text,
                target_country=request.target_country,
                output_style=request.output_style,
                task_type=request.task_type,
            )
        )

        return TextTranslateResponse(
            target_country_ko=result.target_country_ko,
            target_language_ko=result.target_language_ko,
            result_markdown=result.result_markdown,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"텍스트 번역 중 오류가 발생했습니다: {str(e)}",
        )


@app.post("/api/report/translate")
async def translate_report_pdf(
    file: UploadFile = File(...),
    target_country: str = Form(...),
    output_style: str = Form("기획서 문체"),
):
    try:
        pdf_bytes = await file.read()

        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
        ok, message = check_pdf_text_quality(extracted_text)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "PDF에서 텍스트를 추출하지 못했습니다. "
                    "이미지형/PPT형 PDF일 가능성이 큽니다."
                ),
            )

        parsed_document, translated_document = pipeline.run(
            text=extracted_text,
            target_country=target_country,
            output_style=output_style,
        )

        return {
            "message": "번역 완료",
            "text_quality_ok": ok,
            "text_quality_message": message,
            "original_filename": file.filename,
            "original_text": extracted_text,
            "parsed_document": parsed_document.model_dump(),
            "translated_document": translated_document.model_dump(),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"보고서 PDF 번역 중 오류가 발생했습니다: {str(e)}",
        )


@app.post("/api/report/reverse-translate")
async def reverse_translate_report_pdf(
    file: UploadFile = File(...),
    source_country: str = Form(...),
    output_style: str = Form("업무 보고서체"),
):
    try:
        pdf_bytes = await file.read()

        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
        ok, message = check_pdf_text_quality(extracted_text)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "PDF에서 텍스트를 추출하지 못했습니다. "
                    "이미지형/PPT형 PDF일 가능성이 큽니다."
                ),
            )

        parsed_document, translated_document = pipeline.run_to_korean(
            text=extracted_text,
            source_country=source_country,
            output_style=output_style,
        )

        return {
            "message": "한국어 번역 완료",
            "text_quality_ok": ok,
            "text_quality_message": message,
            "original_filename": file.filename,
            "original_text": extracted_text,
            "parsed_document": parsed_document.model_dump(),
            "translated_document": translated_document.model_dump(),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"동남아어 PDF 한국어 번역 중 오류가 발생했습니다: {str(e)}",
        )


@app.post("/api/report/generate-pdf")
def generate_report_pdf(request: PdfGenerateRequest):
    try:
        pdf_bytes = make_universal_report_pdf(
            document=request.translated_document,
            original_filename=request.original_filename,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="translated_report.pdf"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF 생성 중 오류가 발생했습니다: {str(e)}",
        )


@app.post("/api/report/review")
def review_translation(request: ReportReviewRequest):
    try:
        review_result = pipeline.review_translation(
            original_text=request.original_text,
            translated_document=request.translated_document,
            target_country=request.target_country,
        )

        return {
            "message": "번역 검수 완료",
            "review_result": review_result.model_dump(),
            "review_text": review_result_to_text(review_result),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"번역 검수 중 오류가 발생했습니다: {str(e)}",
        )