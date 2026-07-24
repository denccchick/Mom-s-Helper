from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

from app.services.conversion_service import conversion_service

router = APIRouter(tags=["conversion"])

@router.post("/pdf-to-docx")
async def convert_pdf_to_docx(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    docx_path = await conversion_service.pdf_to_docx(file)
    if background_tasks:
        background_tasks.add_task(conversion_service.cleanup, docx_path)
    return FileResponse(
        path=docx_path,
        filename=docx_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.post("/docx-to-pdf")
async def convert_docx_to_pdf(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    pdf_path = await conversion_service.docx_to_pdf(file)
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
    background_tasks: BackgroundTasks = None
):
    docx_path = await conversion_service.pdf2docx_ocr(file)
    if background_tasks:
        background_tasks.add_task(conversion_service.cleanup, docx_path)
    return FileResponse(
        path=docx_path,
        filename=docx_path.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
