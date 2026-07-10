from ctranslate2 import Translator
from pathlib import Path

model_path = Path("./models/nllb-600m-ct2")
translator = Translator(str(model_path), device="cpu")

# Тест 1: без указания языка
result1 = translator.translate_batch([["Hello, how are you?"]])
print(f"Test 1: {result1}")

# Тест 2: с русским языком
result2 = translator.translate_batch([["Hello, how are you?"]], target_prefix=[["rus_Cyrl"]])
print(f"Test 2: {result2}")

# Тест 3: простой текст
result3 = translator.translate_batch([["cat"]])
print(f"Test 3: {result3}")
