import shutil
import asyncio
import os
import io
import numpy as np
from pathlib import Path
from fastapi import UploadFile, HTTPException

from pdf2docx import Converter as PDF2DocxConverter
from docx2pdf import convert as docx2pdf_convert

import fitz  # PyMuPDF
import easyocr
from PIL import Image, ImageDraw

class ConversionService:
    def __init__(self, temp_dir: str = "./tmp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.reader = None

    def load_model(self):
        """Загружает модель EasyOCR. Вызывается один раз при старте сервера."""
        if self.reader is None:
            print("Загрузка модели EasyOCR...")
            # gpu=False или True в зависимости от вашего сервера
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
            print("Модель EasyOCR успешно загружена.")

    def unload(self):
        """Освобождает память при выключении сервера."""
        self.reader = None

    async def pdf_to_docx(self, file: UploadFile) -> Path:
        """Обычная конвертация PDF -> DOCX (для документов, где текст уже выделяется)"""
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
        """Конвертация DOCX -> PDF"""
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

    async def pdf2docx_ocr(self, file: UploadFile) -> Path:
        """Конвертация PDF -> DOCX с использованием OCR"""
        if self.reader is None:
            raise HTTPException(500, "Модель OCR не инициализирована")

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Файл должен быть PDF")

        input_pdf_path = self.temp_dir / f"orig_{file.filename}.tmp"
        ocr_pdf_path = self.temp_dir / f"ocr_{file.filename}.tmp"
        docx_path = self.temp_dir / f"{Path(file.filename).stem}_ocr.docx"

        try:
            with open(input_pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception:
            raise HTTPException(500, "Не удалось сохранить исходный PDF")

        try:
            # Запускаем процесс OCR в отдельном потоке
            await asyncio.to_thread(self._process_ocr_pdf, str(input_pdf_path), str(ocr_pdf_path))

            cv = PDF2DocxConverter(str(ocr_pdf_path))
            cv.convert(str(docx_path), start=0, end=None)
            cv.close()

        except Exception as e:
            raise HTTPException(500, f"Ошибка при обработке OCR/DOCX: {str(e)}")
        finally:
            # Очищаем временные PDF, оставляем только итоговый DOCX
            if input_pdf_path.exists():
                input_pdf_path.unlink()
            if ocr_pdf_path.exists():
                ocr_pdf_path.unlink()

        return docx_path

    def _process_ocr_pdf(self, input_path: str, output_path: str):
        """Синхронный метод для обработки PDF (EasyOCR + PyMuPDF)"""
        CONFIDENCE_THRESHOLD = 0.5

        doc_input = fitz.open(input_path)
        doc_output = fitz.open()

        for page in doc_input:
            new_page = doc_output.new_page(width=page.rect.width, height=page.rect.height)

            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

            results = self.reader.readtext(img_array, detail=1)

            if not results:
                new_page.insert_image(new_page.rect, stream=pix.tobytes("jpeg"))
                continue

            # Закрашиваем старый текст белым
            img_pil = Image.fromarray(img_array)
            draw = ImageDraw.Draw(img_pil)

            for bbox, text, confidence in results:
                if confidence < CONFIDENCE_THRESHOLD:
                    continue

                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]

                padding = 4
                x_min = max(0, min(x_coords) - padding)
                y_min = max(0, min(y_coords) - padding)
                x_max = min(pix.width, max(x_coords) + padding)
                y_max = min(pix.height, max(y_coords) + padding)

                draw.rectangle([x_min, y_min, x_max, y_max], fill=(255, 255, 255))

            # Вставляем очищенный фон
            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format='JPEG', quality=95)
            new_page.insert_image(new_page.rect, stream=img_byte_arr.getvalue())

            # Вставляем новый текст
            scale_x = page.rect.width / pix.width
            scale_y = page.rect.height / pix.height

            font_path = "C:/Windows/Fonts/arial.ttf"
            if os.path.exists(font_path):
                new_page.insert_font(fontname="myfont", fontfile=font_path)
            else:
                new_page.insert_font(fontname="myfont", fontbuffer=fitz.fonts("helv"))

            for bbox, text, confidence in results:
                if confidence < CONFIDENCE_THRESHOLD:
                    continue

                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]

                x_min = min(x_coords) * scale_x
                x_max = max(x_coords) * scale_x
                y_min = min(y_coords) * scale_y
                y_max = max(y_coords) * scale_y

                box_height = y_max - y_min
                box_width = x_max - x_min

                font_size = box_height * 0.70

                estimated_text_width = len(text) * font_size * 0.55 * 1.1
                target_width = max(box_width, estimated_text_width)

                y_padding = 1.5

                text_rect = fitz.Rect(
                    x_min - 1.5,
                    y_min - y_padding,
                    x_min + target_width + 8,
                    y_max + y_padding
                )

                new_page.insert_textbox(
                    text_rect,
                    text,
                    fontsize=font_size,
                    color=(0, 0, 0),
                    fontname="myfont",
                    align=0
                )

        doc_output.save(output_path)
        doc_output.close()
        doc_input.close()

    def cleanup(self, file_path: Path):
        """Удаляет файл после того, как он был отправлен пользователю"""
        if file_path.exists():
            file_path.unlink()

conversion_service = ConversionService()
