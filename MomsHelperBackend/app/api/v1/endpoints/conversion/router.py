from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from app.services.conversion_service import ConversionService

router = APIRouter(tags=["conversion"])
service = ConversionService()

@router.post("/pdf-to-docx")
async def convert_pdf_to_docx(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    docx_path = await service.pdf_to_docx(file)
    if background_tasks:
        background_tasks.add_task(service.cleanup, docx_path)
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
    pdf_path = await service.docx_to_pdf(file)
    if background_tasks:
        background_tasks.add_task(service.cleanup, pdf_path)
    return FileResponse(
        path=pdf_path,
        filename=pdf_path.name,
        media_type="application/pdf"
    )
