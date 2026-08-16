import pytest

from app.services.translation_service import TranslationService


def test_clean_text_removes_problematic_chars():
    svc = TranslationService()
    s = "Hello\u200b World — 2—3  \t"
    out = svc._clean_text(s)
    assert "\u200b" not in out
    assert "2-3" in out


def test_translate_text_without_model_returns_input():
    svc = TranslationService()
    text = "Sample text"
    # When model/tokenizer not loaded, method returns original text
    assert svc.translate_text(text) == text


def test_smart_chunk_splits_long_text():
    svc = TranslationService()
    long = "Sentence one. " + ("A" * 1000) + " End."
    chunks = svc._smart_chunk(long, max_chars=200)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    # Ensure at least one non-empty chunk was produced
    assert any(c.strip() for c in chunks)
