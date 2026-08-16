import pytest
from pathlib import Path
from docx import Document

from app.services.translation_service import TranslationService


@pytest.mark.integration
def test_translate_docx_creates_output(tmp_test_dir, simple_translator):
    # Create a small docx file
    input_path = Path(tmp_test_dir) / "in.docx"
    doc = Document()
    doc.add_paragraph("Hello world")
    doc.add_paragraph("Second paragraph")
    doc.save(input_path)

    out_path = Path(tmp_test_dir) / "out.docx"

    svc = TranslationService()
    # Patch instance translate_text to deterministic russian output for test
    svc.translate_text = simple_translator

    svc.translate_docx(input_path, out_path)

    assert out_path.exists()

    out_doc = Document(out_path)
    joined = "\n".join(p.text for p in out_doc.paragraphs).lower()

    # Check that at least one expected Russian word exists in output
    expected = ["здравствуй", "здравствуйте", "привет", "мир"]
    assert any(w in joined for w in expected)
