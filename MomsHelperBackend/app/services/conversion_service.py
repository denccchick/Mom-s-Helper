import shutil
import tempfile
from pathlib import Path
from fastapi import UploadFile, HTTPException
from pdf2docx import Converter as PDF2DocxConverter
from docx2pdf import convert as docx2pdf_convert

class ConversionService:
    def __init__(self, temp_dir: str = "./tmp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def pdf_to_docx(self, file: UploadFile) -> Path:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Файл должен быть PDF")
        pdf_path = self.temp_dir / f"{file.filename}.tmp"
        try:
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception:
            raise HTTPException(500, "Не удалось сохранить PDF")
        out_name = Path(file.filename).stem + ".docx"
        docx_path = self.temp_dir / out_name
        try:
            cv = PDF2DocxConverter(str(pdf_path))
            cv.convert(str(docx_path), start=0, end=None)
            cv.close()
        except Exception:
            raise HTTPException(500, "Ошибка конвертации PDF → DOCX")
        finally:
            if pdf_path.exists():
                pdf_path.unlink()
        return docx_path

    async def docx_to_pdf(self, file: UploadFile) -> Path:
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(400, "Файл должен быть DOCX")
        docx_path = self.temp_dir / file.filename
        try:
            with open(docx_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception:
            raise HTTPException(500, "Не удалось сохранить DOCX")
        pdf_name = Path(file.filename).stem + ".pdf"
        pdf_path = self.temp_dir / pdf_name
        try:
            docx2pdf_convert(str(docx_path), str(self.temp_dir))
            if not pdf_path.exists():
                raise Exception("PDF не создан")
        except Exception:
            raise HTTPException(500, "Ошибка конвертации DOCX → PDF")
        finally:
            if docx_path.exists():
                docx_path.unlink()
        return pdf_path

    def cleanup(self, file_path: Path):
        if file_path.exists():
            file_path.unlink()
