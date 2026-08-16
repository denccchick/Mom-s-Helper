from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from pathlib import Path
import uuid
import logging
import shutil
import json
import asyncio
from app.services.translation_service import translation_service

router = APIRouter()
logger = logging.getLogger(__name__)

TRANSLATED_DIR = Path("translated_texts")
TRANSLATED_DIR.mkdir(exist_ok=True)

TEMP_DIR = Path("./tmp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/translate-docx")
async def translate_docx(
    file: UploadFile = File(...),
    num_beams: int = Form(2),
):
    """Перевод DOCX с SSE прогрессом (живой перевод)"""
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(400, "Файл должен быть DOCX")

    if num_beams not in (1, 2, 4):
        num_beams = 2

    request_id = str(uuid.uuid4())
    input_path = TEMP_DIR / f"trans_input_{request_id}.docx"
    output_path = TEMP_DIR / f"trans_output_{request_id}.docx"

    original_filename = Path(file.filename).stem

    try:
        with open(input_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"File saved: {input_path}")
    except Exception as e:
        raise HTTPException(500, f"Не удалось сохранить файл: {str(e)}")

    async def event_generator():
        """Генератор SSE событий"""
        try:
            yield f"data: {json.dumps({'progress': 0, 'status': 'Начинаем перевод...'}, ensure_ascii=False)}\n\n"

            message_queue = asyncio.Queue()

            async def send_progress(progress: int, status: str, preview: dict = None):
                data = {'progress': progress, 'status': status}
                if preview:
                    data['preview'] = preview
                message = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                await message_queue.put(message)
                logger.info(f"Progress: {progress}% - {status}")

            translation_service.set_progress_callback(request_id, send_progress)

            translate_task = asyncio.create_task(
                translation_service.translate_docx(
                    input_path, output_path, num_beams, request_id
                )
            )

            while True:
                try:
                    message = await asyncio.wait_for(message_queue.get(), timeout=0.5)
                    yield message
                except asyncio.TimeoutError:
                    if translate_task.done():
                        try:
                            translate_task.result()
                        except Exception as e:
                            logger.error(f"Translation task error: {e}")
                            if "cancelled" in str(e).lower():
                                yield f"data: {json.dumps({'error': 'Операция отменена', 'cancelled': True}, ensure_ascii=False)}\n\n"
                            else:
                                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                            return

                        if output_path.exists():
                            final_filename = f"{original_filename}_{request_id[:8]}_translated.docx"
                            final_path = TRANSLATED_DIR / final_filename
                            shutil.copy2(output_path, final_path)
                            logger.info(f"File saved to: {final_path}")
                            download_url = f"/api/v1/translation/download/{final_filename}"
                        else:
                            logger.error("Output file not found!")
                            download_url = None

                        yield f"data: {json.dumps({
                            'done': True,
                            'download_url': download_url,
                            'filename': final_filename if output_path.exists() else None,
                            'progress': 100,
                            'status': 'Готово!'
                        }, ensure_ascii=False)}\n\n"
                        return

                    yield f"data: {json.dumps({'type': 'ping'}, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            logger.info(f"Event generator cancelled for {request_id}")
            translation_service.cancel_request(request_id)
        except Exception as e:
            logger.error(f"Event generator error: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            translation_service.remove_progress_callback(request_id)
            try:
                if input_path.exists():
                    input_path.unlink()
                    logger.info(f"Deleted input: {input_path}")
            except:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/cancel/{request_id}")
async def cancel_translation(request_id: str):
    """Отмена перевода"""
    translation_service.cancel_request(request_id)
    return {"status": "cancelled"}


@router.get("/download/{filename}")
async def download_translation(filename: str):
    """Скачать переведённый файл"""
    file_path = TRANSLATED_DIR / filename
    if not file_path.exists():
        file_path = TEMP_DIR / filename

    if not file_path.exists():
        raise HTTPException(404, f"Файл '{filename}' не найден")

    logger.info(f"Downloading file: {file_path}")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/files")
async def list_translation_files():
    """Список всех переведённых файлов"""
    try:
        files = []
        for file_path in TRANSLATED_DIR.glob("*_translated.docx"):
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "created": file_path.stat().st_ctime
            })
        files.sort(key=lambda x: x["created"], reverse=True)
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/translate-text")
async def translate_text(text: str = Form(...)):
    """Перевод текста"""
    return {"translated": translation_service.translate_text(text)}


@router.get("/test")
async def test_endpoint():
    """Тестовый эндпоинт"""
    logger.info("Test endpoint called!")
    return {"status": "ok", "message": "Translation router works!"}
