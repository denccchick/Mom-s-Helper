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
    svc.unload()
    svc.translate_text = TranslationService.translate_text.__get__(svc, TranslationService)
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


def test_translate_chunk_passes_num_beams_to_model(monkeypatch):
    svc = TranslationService()
    svc._tokenizer = type("Tok", (), {})()
    svc._tokenizer.src_lang = "eng_Latn"
    svc._tokenizer.encode = lambda text: [1, 2, 3]
    svc._tokenizer.convert_ids_to_tokens = lambda ids: ["A", "B", "C"]
    svc._tokenizer.convert_tokens_to_ids = lambda tokens: [1, 2, 3]
    svc._tokenizer.decode = lambda ids: "translated"

    captured = {}

    class FakeTranslator:
        def translate_batch(self, batch, target_prefix, max_decoding_length, beam_size=None):
            captured["beam_size"] = beam_size
            return [type("Res", (), {"hypotheses": [["rus_Cyrl", "translated"]]})()]

    svc._translator = FakeTranslator()

    result = svc._translate_chunk("hello", "eng_Latn", "rus_Cyrl", num_beams=4)

    assert result == "translated"
    assert captured["beam_size"] == 4
