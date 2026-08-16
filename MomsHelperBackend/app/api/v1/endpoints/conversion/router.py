from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import asyncio
import uuid
import json
from pathlib import Path
from app.services.conversion_service import conversion_service
from datetime import datetime

router = APIRouter(tags=["conversion"])

@router.post("/pdf-to-docx")
def convert_pdf_to_docx(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):

    docx_path, preview_images = conversion_service.pdf_to_docx(file)

    return JSONResponse({
        "success": True,
        "file_path": str(docx_path),
        "filename": docx_path.name,
        "preview": preview_images
    })

@router.post("/docx-to-pdf")
def convert_docx_to_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):

    pdf_path, preview_images = conversion_service.docx_to_pdf(file)

    # Возвращаем JSON с информацией о файле и превью
    return JSONResponse({
        "success": True,
        "file_path": str(pdf_path),
        "filename": pdf_path.name,
        "preview": preview_images
    })

@router.post("/pdf-to-docx-ocr")
async def convert_pdf_to_docx_ocr(
    file: UploadFile = File(...),
    request_id: str = Query(None),
    background_tasks: BackgroundTasks = None
):
    if not request_id:
        request_id = str(uuid.uuid4())
    docx_path = await conversion_service.pdf2docx_ocr(file, request_id)
    if background_tasks:
        background_tasks.add_task(conversion_service.remove_progress_callback, request_id)

    # Возвращаем JSON с информацией о файле
    return JSONResponse({
        "success": True,
        "file_path": str(docx_path),
        "filename": docx_path.name,
        "preview": []
    })

@router.get("/download/{filename}")
def download_file(filename: str):
    safe_name = Path(filename).name
    path = (conversion_service.temp_dir / safe_name).resolve()

    if not path.exists() or not path.is_file():
        raise HTTPException(404, f"Файл не найден: {filename}")

    if conversion_service.temp_dir.resolve() not in path.parents and path.resolve() != conversion_service.temp_dir.resolve():
        raise HTTPException(403, "Недопустимый путь к файлу")

    extension = path.suffix.lower()
    if extension == '.pdf':
        media_type = "application/pdf"
    elif extension == '.docx':
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        media_type = "application/octet-stream"

    print(f"Serving file: {path} (size: {path.stat().st_size} bytes)")

    return FileResponse(
        path=path,
        filename=path.name,
        media_type=media_type
    )

@router.post("/cancel/{request_id}")
async def cancel_conversion(request_id: str):
    conversion_service.cancel_request(request_id)
    return {"status": "cancelled", "request_id": request_id}

@router.get("/progress/{request_id}")
async def get_progress(request_id: str):
    async def event_generator():
        queue = asyncio.Queue()

        async def progress_callback(progress: int, status: str = "", preview: dict = None):
            data = {"progress": progress, "status": status}
            if preview:
                data["preview"] = preview
            await queue.put(data)

        conversion_service.set_progress_callback(request_id, progress_callback)

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data["progress"] >= 100:
                        break
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
        finally:
            conversion_service.remove_progress_callback(request_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.get("/files")
def list_files():
    """Список всех временных файлов (для отладки)"""
    files = []
    for file_path in conversion_service.temp_dir.glob("*"):
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            })
    return {
        "count": len(files),
        "files": files,
        "temp_dir": str(conversion_service.temp_dir)
    }
