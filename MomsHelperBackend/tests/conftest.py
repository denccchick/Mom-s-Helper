import io
import shutil
from types import SimpleNamespace
from pathlib import Path

import pytest


def make_uploadfile(filename: str, content: bytes):
    return SimpleNamespace(filename=filename, file=io.BytesIO(content))


@pytest.fixture
def uploadfile_factory():
    return make_uploadfile


@pytest.fixture
def tmp_test_dir(tmp_path):
    d = tmp_path / "tmp"
    d.mkdir()
    yield d
    # ensure cleanup after tests
    if d.exists():
        try:
            shutil.rmtree(d)
        except Exception:
            pass


@pytest.fixture
def simple_translator():
    """Returns a simple translation function used in integration tests.

    It maps common English greetings to Russian words so tests can assert
    that a translation has occurred without loading a real model.
    """
    def _translate(text: str, src_lang: str = None, tgt_lang: str = None, num_beams: int = 2):
        low = text.lower()
        if "hello" in low and "world" in low:
            return "Привет мир"
        if "hello" in low:
            return "Привет"
        return text + " (ru)"

    return _translate
