import shutil
import asyncio
import os
import io
import base64
import numpy as np
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional, Callable, Set
from datetime import datetime

from pdf2docx import Converter as PDF2DocxConverter
from docx2pdf import convert as docx2pdf_convert

import fitz
import easyocr
from PIL import Image, ImageDraw

class ConversionService:
    def __init__(self, temp_dir: str = "./tmp"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.reader = None
        self.progress_callbacks = {}
        self.cancelled_requests: Set[str] = set()
        self.main_loop = None
        self._cleanup_old_files()

    def _cleanup_old_files(self):
        try:
            now = datetime.now()
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    file_age = (now - datetime.fromtimestamp(file_path.stat().st_mtime)).total_seconds()
                    if file_age > 3600:
                        try:
                            file_path.unlink()
                        except:
                            pass
        except:
            pass

    def cancel_request(self, request_id: str):
        self.cancelled_requests.add(request_id)

    def is_cancelled(self, request_id: str) -> bool:
        return request_id in self.cancelled_requests

    def load_model(self):
        if self.reader is None:
            print("Загрузка модели EasyOCR...")
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
            print("Модель EasyOCR успешно загружена.")

    def unload(self):
        self.reader = None
        self.cancelled_requests.clear()

    def set_progress_callback(self, request_id: str, callback: Callable):
        self.progress_callbacks[request_id] = callback

    def remove_progress_callback(self, request_id: str):
        if request_id in self.progress_callbacks:
            del self.progress_callbacks[request_id]
        if request_id in self.cancelled_requests:
            self.cancelled_requests.remove(request_id)

    async def update_progress(self, request_id: str, progress: int, status: str = "", preview: dict = None):
        if self.is_cancelled(request_id):
            raise Exception("Operation cancelled")
        if request_id in self.progress_callbacks:
            callback = self.progress_callbacks[request_id]
            await callback(progress, status, preview)

    def _page_to_base64(self, page) -> dict:
        try:
            pix = page.get_pixmap(dpi=100)
            img_bytes = pix.tobytes("jpeg")
            return {
                "base64": base64.b64encode(img_bytes).decode('utf-8'),
                "width": pix.width,
                "height": pix.height
            }
        except Exception as e:
            print(f"Error in _page_to_base64: {e}")
            return {"base64": "", "width": 0, "height": 0}

    def _cleanup_files(self, *paths):
        for path in paths:
            if path and Path(path).exists():
                try:
                    Path(path).unlink()
                except:
                    pass

    def pdf_to_docx(self, file: UploadFile) -> tuple[Path, list]:
        """Синхронная конвертация PDF→DOCX с превью"""
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Файл должен быть PDF")

        pdf_path = self.temp_dir / f"{file.filename}.tmp"
        try:
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            self._cleanup_files(pdf_path)
            raise HTTPException(500, f"Не удалось сохранить PDF: {str(e)}")

        out_name = Path(file.filename).stem + ".docx"
        docx_path = self.temp_dir / out_name

        try:
            cv = PDF2DocxConverter(str(pdf_path))
            cv.convert(str(docx_path), start=0, end=None)
            cv.close()
        except Exception as e:
            self._cleanup_files(pdf_path, docx_path)
            raise HTTPException(500, f"Ошибка конвертации PDF → DOCX: {str(e)}")
        finally:
            self._cleanup_files(pdf_path)

        preview_images = self._docx_to_preview_images(str(docx_path), 3)

        return docx_path, preview_images

    def docx_to_pdf(self, file: UploadFile) -> Path:
        """Синхронная конвертация DOCX→PDF"""
        if not file.filename.lower().endswith('.docx'):
            raise HTTPException(400, "Файл должен быть DOCX")

        docx_path = self.temp_dir / file.filename
        try:
            with open(docx_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            self._cleanup_files(docx_path)
            raise HTTPException(500, f"Не удалось сохранить DOCX: {str(e)}")

        pdf_name = Path(file.filename).stem + ".pdf"
        pdf_path = self.temp_dir / pdf_name

        try:
            docx2pdf_convert(str(docx_path), str(self.temp_dir))
            if not pdf_path.exists():
                raise Exception("PDF не создан")
        except Exception as e:
            self._cleanup_files(docx_path, pdf_path)
            raise HTTPException(500, f"Ошибка конвертации DOCX → PDF: {str(e)}")
        finally:
            self._cleanup_files(docx_path)

        return pdf_path

    def _docx_to_preview_images(self, docx_path: str, max_pages: int = 3) -> list:
        """Генерирует превью из DOCX"""
        try:
            pdf_path = Path(docx_path).with_suffix('.pdf')
            docx2pdf_convert(docx_path, str(pdf_path.parent))

            if not pdf_path.exists():
                return []

            doc = fitz.open(str(pdf_path))
            total_pages = min(len(doc), max_pages)
            images = []

            for page_num in range(total_pages):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=100)
                img_bytes = pix.tobytes("jpeg")
                images.append({
                    "base64": base64.b64encode(img_bytes).decode('utf-8'),
                    "width": pix.width,
                    "height": pix.height
                })

            doc.close()
            self._cleanup_files(pdf_path)
            return images

        except Exception as e:
            print(f"Error generating preview from DOCX: {e}")
            return []


    async def pdf2docx_ocr(self, file: UploadFile, request_id: str = None) -> Path:
        """Асинхронная конвертация PDF→DOCX с OCR и SSE прогрессом"""
        if self.reader is None:
            raise HTTPException(500, "Модель OCR не инициализирована")

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(400, "Файл должен быть PDF")

        if self.main_loop is None:
            self.main_loop = asyncio.get_running_loop()

        if request_id:
            await self.update_progress(request_id, 5, "Проверка файла...")

        input_pdf_path = self.temp_dir / f"orig_{file.filename}.tmp"
        ocr_pdf_path = self.temp_dir / f"ocr_{file.filename}.tmp"
        docx_path = self.temp_dir / f"{Path(file.filename).stem}_ocr.docx"

        try:
            with open(input_pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            if request_id:
                await self.update_progress(request_id, 15, "Файл загружен")
        except Exception as e:
            self._cleanup_files(input_pdf_path)
            raise HTTPException(500, f"Не удалось сохранить исходный PDF: {str(e)}")

        try:
            if request_id:
                await self.update_progress(request_id, 20, "Запуск OCR...")

            # Запускаем OCR в отдельном потоке с передачей event loop
            await asyncio.to_thread(self._process_ocr_pdf, str(input_pdf_path), str(ocr_pdf_path), request_id, self.main_loop)

            if self.is_cancelled(request_id):
                self._cleanup_files(input_pdf_path, ocr_pdf_path, docx_path)
                raise Exception("Operation cancelled")

            if request_id:
                await self.update_progress(request_id, 85, "Конвертация в DOCX...")

            cv = PDF2DocxConverter(str(ocr_pdf_path))
            cv.convert(str(docx_path), start=0, end=None)
            cv.close()

            if request_id:
                await self.update_progress(request_id, 98, "Сохранение файла...")

        except Exception as e:
            self._cleanup_files(input_pdf_path, ocr_pdf_path, docx_path)
            if str(e) == "Operation cancelled":
                raise HTTPException(499, "Операция отменена пользователем")
            raise HTTPException(500, f"Ошибка при обработке OCR/DOCX: {str(e)}")
        finally:
            self._cleanup_files(input_pdf_path, ocr_pdf_path)

        if request_id:
            await self.update_progress(request_id, 100, "Готово!")

        return docx_path

    def _process_ocr_pdf(self, input_path: str, output_path: str, request_id: str = None, loop=None):
        """Синхронная обработка OCR в отдельном потоке"""
        CONFIDENCE_THRESHOLD = 0.5

        doc_input = fitz.open(input_path)
        doc_output = fitz.open()
        total_pages = len(doc_input)

        for page_num, page in enumerate(doc_input):
            if request_id and self.is_cancelled(request_id):
                doc_input.close()
                doc_output.close()
                self._cleanup_files(output_path)
                raise Exception("Operation cancelled")

            new_page = doc_output.new_page(width=page.rect.width, height=page.rect.height)

            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

            results = self.reader.readtext(img_array, detail=1)

            if not results:
                new_page.insert_image(new_page.rect, stream=pix.tobytes("jpeg"))
                if request_id:
                    progress = 20 + int((page_num + 1) / total_pages * 60)
                    preview_data = self._page_to_base64(new_page)
                    self._send_progress_sync(request_id, progress, f"Страница {page_num + 1}/{total_pages}", preview_data, loop)
                continue

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

            img_byte_arr = io.BytesIO()
            img_pil.save(img_byte_arr, format='JPEG', quality=95)
            new_page.insert_image(new_page.rect, stream=img_byte_arr.getvalue())

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

            if request_id:
                progress = 20 + int((page_num + 1) / total_pages * 60)
                preview_data = self._page_to_base64(new_page)
                self._send_progress_sync(request_id, progress, f"Страница {page_num + 1}/{total_pages}", preview_data, loop)

        doc_output.save(output_path)
        doc_output.close()
        doc_input.close()

    def _send_progress_sync(self, request_id: str, progress: int, status: str, preview: dict = None, loop=None):
        """Синхронная отправка прогресса из потока"""
        try:
            if request_id in self.progress_callbacks and loop is not None:
                callback = self.progress_callbacks[request_id]
                asyncio.run_coroutine_threadsafe(
                    callback(progress, status, preview),
                    loop
                )
        except Exception as e:
            print(f"Error sending progress: {e}")

    def cleanup(self, file_path: Path):
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except:
                pass

conversion_service = ConversionService()
