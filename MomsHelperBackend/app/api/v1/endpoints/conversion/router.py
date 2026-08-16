from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
import asyncio
import uuid
import json
from pathlib import Path
from app.services.conversion_service import conversion_service

router = APIRouter(tags=["conversion"])


@router.post("/pdf-to-docx")
def convert_pdf_to_docx(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    docx_path, preview_images = conversion_service.pdf_to_docx(file)

    if background_tasks:
        background_tasks.add_task(conversion_service.cleanup, docx_path)

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
    pdf_path = conversion_service.docx_to_pdf(file)
    if background_tasks:
        background_tasks.add_task(conversion_service.cleanup, pdf_path)
    return FileResponse(
        path=pdf_path,
        filename=pdf_path.name,
        media_type="application/pdf"
    )


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
        background_tasks.add_task(conversion_service.cleanup, docx_path)
        background_tasks.add_task(conversion_service.remove_progress_callback, request_id)
    return FileResponse(
        path=docx_path,
        filename=docx_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.get("/download/{file_path:path}")
def download_file(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(404, "Файл не найден")
    return FileResponse(
        path=path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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
