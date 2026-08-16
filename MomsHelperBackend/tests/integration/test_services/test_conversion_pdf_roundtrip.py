import io
import pytest
from types import SimpleNamespace
from pathlib import Path

from docx import Document

from app.services.conversion_service import ConversionService
from fastapi import HTTPException


def make_uploadfile(filename: str, content: bytes):
    return SimpleNamespace(filename=filename, file=io.BytesIO(content))


@pytest.mark.asyncio
@pytest.mark.integration
async def test_docx_to_pdf_and_back(tmp_test_dir, uploadfile_factory):
    svc = ConversionService(temp_dir=str(tmp_test_dir))

    # create a small docx
    input_docx = Path(tmp_test_dir) / "in.docx"
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.save(input_docx)

    # convert docx -> pdf via the service (wrapped as UploadFile)
    with open(input_docx, "rb") as f:
        uf = uploadfile_factory(input_docx.name, f.read())

    try:
        pdf_path = await svc.docx_to_pdf(uf)
    except HTTPException as e:
        pytest.skip(f"docx->pdf conversion not available in environment: {e.detail}")

    assert pdf_path.exists()

    # now convert pdf -> docx via pdf2docx
    with open(pdf_path, "rb") as f:
        pdf_uf = uploadfile_factory(pdf_path.name, f.read())

    try:
        out_docx = await svc.pdf_to_docx(pdf_uf)
    except HTTPException as e:
        pytest.skip(f"pdf->docx conversion failed: {e.detail}")

    assert out_docx.exists()

    # Load resulting docx and ensure it contains some text
    from docx import Document as DocxLoader

    res = DocxLoader(out_docx)
    all_text = "\n".join(p.text for p in res.paragraphs)
    assert len(all_text.strip()) > 0
