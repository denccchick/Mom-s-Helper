import logging
import re
import psutil
import torch
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
    _using_8bit = False
    _using_ct2 = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self, model_path: Path, device: str = "cpu"):
        if self._translator is not None:
            logger.info("Model already loaded")
            return self._translator

        available_ram = psutil.virtual_memory().available / (1024 ** 3)
        total_ram = psutil.virtual_memory().total / (1024 ** 3)
        logger.info(f"RAM: {total_ram:.1f} GB total, {available_ram:.1f} GB available")

        # Проверяем, есть ли файлы CTranslate2
        is_ct2 = self._is_ct2_model(model_path)

        if is_ct2:
            logger.info("CTranslate2 model detected, loading directly...")
            self._load_ct2(model_path, device)
        elif available_ram < 3.0:
            logger.warning(f"Low memory ({available_ram:.1f} GB), using 8-bit mode...")
            self._load_transformers_8bit(model_path)
        else:
            logger.info(f"Sufficient memory ({available_ram:.1f} GB), loading full model...")
            self._load_transformers_full(model_path)

        return self._translator

    def _is_ct2_model(self, model_path: Path) -> bool:
        try:
            files = list(model_path.glob("*.ct2")) or list(model_path.glob("*_vocabulary.json"))
            return len(files) > 0
        except:
            return False

    def _load_ct2(self, model_path: Path, device: str):
        logger.info(f"Loading CTranslate2 from {model_path}")
        self._translator = Translator(str(model_path), device=device, compute_type="int8")
        self._tokenizer = AutoTokenizer.from_pretrained(str(model_path), src_lang="eng_Latn")
        self._using_ct2 = True
        self._using_8bit = False
        logger.info("✅ CTranslate2 loaded (most memory efficient)")

    def _load_transformers_8bit(self, model_path: Path):
        logger.info(f"Loading transformers 8-bit from {model_path}")
        try:
            from transformers import AutoModelForSeq2SeqLM
            self._tokenizer = AutoTokenizer.from_pretrained(str(model_path), src_lang="eng_Latn")

            try:
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    str(model_path),
                    load_in_8bit=True,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    torch_dtype=torch.float16
                )
                self._using_8bit = True
                logger.info("✅ 8-bit model loaded")
            except (ImportError, RuntimeError):
                logger.warning("bitsandbytes not available, using float16")
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    str(model_path),
                    low_cpu_mem_usage=True,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                self._using_8bit = False
                logger.info("✅ float16 model loaded")

            # CTranslate2 не используется, но translator нужен для совместимости API
            self._translator = model
            self._using_ct2 = False

        except Exception as e:
            logger.error(f"Failed to load transformers: {e}")
            raise

    def _load_transformers_full(self, model_path: Path):
        logger.info(f"Loading full transformers from {model_path}")
        from transformers import AutoModelForSeq2SeqLM
        self._tokenizer = AutoTokenizer.from_pretrained(str(model_path), src_lang="eng_Latn")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            str(model_path),
            low_cpu_mem_usage=True,
            device_map="auto"
        )
        self._translator = model
        self._using_ct2 = False
        self._using_8bit = False
        logger.info("✅ Full model loaded")

    def _clean_text(self, text: str) -> str:
        if not text:
            return text
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        replacements = {'¬': '', '\u200b': '', '\u200c': '', '\u200d': '', '\ufeff': ''}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r'(\d)\s*[—–−]\s*(\d)', r'\1-\2', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def _post_process_typography(self, text: str) -> str:
        if not text:
            return text
        text = re.sub(r' - ', ' — ', text)
        return text

    def _smart_chunk(self, text: str, max_chars: int = 800) -> list[str]:
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

            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _translate_chunk_ct2(self, chunk: str, src_lang: str, tgt_lang: str) -> str:
        if not chunk.strip():
            return ""

        try:
            self._tokenizer.src_lang = src_lang
            input_tokens = self._tokenizer.encode(chunk)
            tokens = self._tokenizer.convert_ids_to_tokens(input_tokens)

            if not tokens:
                return ""

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
            return self._tokenizer.decode(output_ids).strip()

        except Exception as e:
            logger.error(f"CT2 chunk error: {e}")
            return chunk

    def _translate_chunk_transformers(self, chunk: str, src_lang: str, tgt_lang: str) -> str:
        if not chunk.strip():
            return ""

        try:
            inputs = self._tokenizer(
                chunk,
                src_lang=src_lang,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                generated = self._translator.generate(
                    **inputs,
                    forced_bos_token_id=self._tokenizer.lang_code_to_id[tgt_lang],
                    max_length=1024
                )

            return self._tokenizer.decode(generated[0], skip_special_tokens=True).strip()

        except Exception as e:
            logger.error(f"Transformers chunk error: {e}")
            return chunk

    def translate_text(self, text: str, src_lang: str = "eng_Latn", tgt_lang: str = "rus_Cyrl") -> str:
        if not text or not text.strip():
            return text

        if self._translator is None or self._tokenizer is None:
            logger.error("Model not loaded")
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
                if self._using_ct2:
                    translated = self._translate_chunk_ct2(chunk, src_lang, tgt_lang)
                else:
                    translated = self._translate_chunk_transformers(chunk, src_lang, tgt_lang)
                translated_chunks.append(translated)

            translated_lines.append(" ".join(translated_chunks))

        final_text = "\n".join(translated_lines)
        return self._post_process_typography(final_text)

    def _preserve_runs_formatting(self, paragraph: Paragraph, translated_text: str) -> None:
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
        logger.info(f"Saved to {output_path}")
        return output_path

    def unload(self):
        self._translator = None
        self._tokenizer = None
        self._using_ct2 = False
        self._using_8bit = False
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        logger.info("Model unloaded")


translation_service = TranslationService()
