import io
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.services.conversion_service import ConversionService
from fastapi import HTTPException


def make_uploadfile(filename: str, content: bytes):
    return SimpleNamespace(filename=filename, file=io.BytesIO(content))


@pytest.mark.asyncio
async def test_pdf_to_docx_invalid_extension():
    svc = ConversionService(temp_dir="./tmp_test_cs")
    uf = make_uploadfile("not_a_pdf.txt", b"abc")

    with pytest.raises(HTTPException) as exc:
        await svc.pdf_to_docx(uf)

    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_docx_to_pdf_invalid_extension():
    svc = ConversionService(temp_dir="./tmp_test_cs")
    uf = make_uploadfile("not_a_pdf.pdf", b"abc")

    # docx_to_pdf requires a .docx filename
    with pytest.raises(HTTPException) as exc:
        await svc.docx_to_pdf(make_uploadfile("bad.doc", b"doc"))

    assert exc.value.status_code == 400


def test_cleanup_removes_file(tmp_path):
    svc = ConversionService(temp_dir=str(tmp_path))
    p = Path(tmp_path) / "to_remove.tmp"
    p.write_bytes(b"x")
    assert p.exists()
    svc.cleanup(p)
    assert not p.exists()
