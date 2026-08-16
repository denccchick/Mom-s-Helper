from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import logging
from app.services.translation_service import translation_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Создаем папку для сохранения переведенных файлов
TRANSLATED_DIR = Path("translated_texts")
TRANSLATED_DIR.mkdir(exist_ok=True)


@router.post("/translate-docx")
async def translate_docx(
    file: UploadFile = File(...),
    num_beams: int = Form(2),
):
    if not file.filename.endswith('.docx'):
        raise HTTPException(400, "Only DOCX files are supported")

    if num_beams not in (1, 2, 4):
        raise HTTPException(400, "num_beams must be one of: 1, 2, 4")

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(await file.read())
        input_path = Path(tmp.name)

    try:
        original_name = Path(file.filename).stem
        unique_id = uuid.uuid4().hex[:8]
        output_filename = f"{original_name}_{unique_id}_translated.docx"
        output_path = TRANSLATED_DIR / output_filename

        logger.info(f"Saving translated document to: {output_path} with num_beams={num_beams}")

        result = translation_service.translate_docx(input_path, output_path, num_beams=num_beams)

        if not result.exists():
            raise HTTPException(500, "File was not saved successfully")

        logger.info(f"File saved successfully. Size: {result.stat().st_size} bytes")

        return FileResponse(
            path=result,
            filename=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(500, f"Translation failed: {str(e)}")
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/translate-text")
async def translate_text(text: str):
    return {"translated": translation_service.translate_text(text)}


@router.get("/health")
async def health_check():
    try:
        translation_service.translate_text("test")
        return {"status": "ok", "model_loaded": translation_service._translator is not None}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/list-translations")
async def list_translations():
    """Получить список всех сохраненных переводов"""
    try:
        files = []
        for file_path in TRANSLATED_DIR.glob("*.docx"):
            files.append({
                "filename": file_path.name,
                "size_bytes": file_path.stat().st_size,
                "created": file_path.stat().st_ctime,
                "path": str(file_path)
            })
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/download/{filename}")
async def download_translation(filename: str):
    """Скачать сохраненный перевод по имени файла"""
    file_path = TRANSLATED_DIR / filename

    if not file_path.exists():
        raise HTTPException(404, f"File '{filename}' not found")

    if not file_path.is_relative_to(TRANSLATED_DIR):
        raise HTTPException(403, "Access denied")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
