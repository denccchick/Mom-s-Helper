import io
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.services.conversion_service import ConversionService
from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont


def _make_image_pdf(path: Path, text: str = "Hello world"):
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = None
    draw.text((20, 60), text, fill=(0, 0, 0), font=font)
    img.save(path, "PDF")


class DummyReader:
    def readtext(self, img_array, detail=1):
        bbox = [(10, 10), (300, 10), (300, 80), (10, 80)]
        return [(bbox, "Hello world", 0.98)]


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


def test__process_ocr_pdf_creates_output(tmp_path):
    svc = ConversionService(temp_dir=str(tmp_path))

    input_pdf = tmp_path / "img.pdf"
    ocr_output_pdf = tmp_path / "ocr_out.pdf"

    _make_image_pdf(input_pdf, text="Hello world")

    svc.reader = DummyReader()

    svc._process_ocr_pdf(str(input_pdf), str(ocr_output_pdf))

    assert ocr_output_pdf.exists()
    assert ocr_output_pdf.stat().st_size > 0
