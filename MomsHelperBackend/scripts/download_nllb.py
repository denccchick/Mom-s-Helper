import os
from huggingface_hub import HfApi, snapshot_download

# На всякий случай отключаем зеркала, так как ваша прямая связь с HF работает (вы залогинились)
if "HF_ENDPOINT" in os.environ:
    del os.environ["HF_ENDPOINT"]

output_dir = "./models/nllb-600m-ct2"
os.makedirs(output_dir, exist_ok=True)

api = HfApi()
print("🔍 Ищу доступные CTranslate2 версии модели на серверах Hugging Face...")

try:
    # Ищем все репозитории с названием оригинальной модели
    models = list(api.list_models(search="nllb-200-distilled-600M"))

    best_repo = None
    for m in models:
        # Проверяем, что в названии есть 'ct2' (конвертированная версия)
        if "ct2" in m.id.lower() or "ctranslate" in m.id.lower():
            best_repo = m.id
            break

    if best_repo is None:
        print("❌ Не найдено ни одного публичного репозитория.")
    else:
        print(f"✅ Найден живой репозиторий: {best_repo}")
        print(f"⏳ Скачиваю файлы в {output_dir}...")

        # Скачиваем найденную модель
        snapshot_download(
            repo_id=best_repo,
            local_dir=output_dir,
            local_dir_use_symlinks=False
        )
        print(f"\n🎉 ВСЁ УСПЕШНО! Модель загружена и готова к работе.")

except Exception as e:
    print(f"❌ Произошла ошибка: {e}")
