import logging
import re
from pathlib import Path
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from ctranslate2 import Translator
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


class TranslationService:
    _instance = None
    _translator = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self, model_path: Path, device: str = "cpu"):
        if self._translator is None:
            logger.info(f"Loading model and tokenizer from {model_path}")
            self._translator = Translator(str(model_path), device=device, compute_type="int8")
            self._tokenizer = AutoTokenizer.from_pretrained(str(model_path), src_lang="eng_Latn")
            logger.info("Model and tokenizer loaded successfully")
        return self._translator

    def _clean_text(self, text: str) -> str:
        """Умная очистка: убирает мусор и спасает токенизатор от <unk>"""
        if not text:
            return text

        # Удаляем системные символы, кроме \n
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

        # Заменяем проблемные символы на безопасные
        replacements = {
            '¬': '', '\u200b': '', '\u200c': '', '\u200d': '', '\ufeff': ''
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # Нормализуем диапазоны чисел (2—3 -> 2-3)
        text = re.sub(r'(\d)\s*[—–−]\s*(\d)', r'\1-\2', text)

        # Сжимаем пробелы
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    def _post_process_typography(self, text: str) -> str:
        """Возвращает нормальную русскую пунктуацию (длинные тире)"""
        if not text:
            return text
        # Заменяем дефисы, окруженные пробелами, на длинное тире
        text = re.sub(r' - ', ' — ', text)
        return text

    def _smart_chunk(self, text: str, max_chars: int = 800) -> list[str]:
        """Семантический чанкинг: бьет текст на куски, сохраняя целые предложения"""
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if not sentence.strip():
                continue

            if len(sentence) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Если предложение гигантское, рубим по запятым
                sub_chunks = re.split(r'(?<=[,;])\s+', sentence)
                temp_chunk = ""
                for sub in sub_chunks:
                    if len(temp_chunk) + len(sub) > max_chars:
                        chunks.append(temp_chunk.strip())
                        temp_chunk = sub + " "
                    else:
                        temp_chunk += sub + " "
                if temp_chunk:
                    current_chunk = temp_chunk
                continue

            # Складываем предложения в чанк
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _translate_chunk(self, chunk: str, src_lang: str, tgt_lang: str) -> str:
        """Перевод отдельного чанка"""
        if not chunk.strip():
            return ""

        try:
            self._tokenizer.src_lang = src_lang
            input_tokens = self._tokenizer.encode(chunk)
            tokens = self._tokenizer.convert_ids_to_tokens(input_tokens)

            if not tokens:
                return ""

            # max_decoding_length=1024 - РЕШАЕТ ПРОБЛЕМУ ОБРЕЗКИ ТЕКСТА
            results = self._translator.translate_batch(
                [tokens],
                target_prefix=[[tgt_lang]],
                max_decoding_length=1024
            )

            if not results or not results[0].hypotheses:
                return chunk

            hypothesis = results[0].hypotheses[0]

            if hypothesis and hypothesis[0] == tgt_lang:
                hypothesis = hypothesis[1:]

            output_ids = self._tokenizer.convert_tokens_to_ids(hypothesis)
            result_text = self._tokenizer.decode(output_ids)

            return result_text.strip()

        except Exception as e:
            logger.error(f"Chunk translation error: {e}")
            return chunk

    def translate_text(self, text: str, src_lang: str = "eng_Latn", tgt_lang: str = "rus_Cyrl") -> str:
        """Главный метод перевода текста с сохранением структуры"""
        if not text or not text.strip():
            return text

        if self._translator is None or self._tokenizer is None:
            logger.error("Model is not loaded! Call load_model() first.")
            return text

        lines = text.splitlines()
        translated_lines = []

        for line in lines:
            if not line.strip():
                translated_lines.append("")
                continue

            clean_line = self._clean_text(line)
            chunks = self._smart_chunk(clean_line, max_chars=400)

            translated_chunks = []
            for chunk in chunks:
                translated = self._translate_chunk(chunk, src_lang, tgt_lang)
                translated_chunks.append(translated)

            translated_lines.append(" ".join(translated_chunks))

        final_text = "\n".join(translated_lines)
        return self._post_process_typography(final_text)

    def _preserve_runs_formatting(self, paragraph: Paragraph, translated_text: str) -> None:
        """Сохранение форматирования DOCX"""
        if not paragraph.runs:
            paragraph.text = translated_text
            return

        if len(paragraph.runs) == 1:
            paragraph.runs[0].text = translated_text
            return

        first_run = paragraph.runs[0]
        original_style = first_run.style
        original_bold = first_run.bold
        original_italic = first_run.italic
        original_underline = first_run.underline
        original_font = first_run.font

        for run in paragraph.runs:
            run.text = ""

        new_run = paragraph.runs[0]
        new_run.text = translated_text

        if original_style:
            new_run.style = original_style
        if original_bold is not None:
            new_run.bold = original_bold
        if original_italic is not None:
            new_run.italic = original_italic
        if original_underline is not None:
            new_run.underline = original_underline
        if original_font:
            new_run.font.name = original_font.name
            new_run.font.size = original_font.size

    def translate_paragraph(self, paragraph: Paragraph) -> None:
        original_text = paragraph.text
        if not original_text or not original_text.strip():
            return

        translated_text = self.translate_text(original_text)
        self._preserve_runs_formatting(paragraph, translated_text)

    def translate_table(self, table: Table) -> None:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    self.translate_paragraph(paragraph)
                for nested_table in cell.tables:
                    self.translate_table(nested_table)

    def translate_docx(self, input_path: Path, output_path: Path) -> Path:
        doc = Document(input_path)

        for paragraph in doc.paragraphs:
            self.translate_paragraph(paragraph)

        for table in doc.tables:
            self.translate_table(table)

        doc.save(output_path)
        logger.info(f"Translated document saved to {output_path}")
        return output_path

    def unload(self):
        self._translator = None
        self._tokenizer = None
        logger.info("Model unloaded")


translation_service = TranslationService()
