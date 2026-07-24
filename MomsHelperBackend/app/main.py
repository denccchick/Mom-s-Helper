from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import psutil
import traceback
import asyncio


from app.api.router import setup_routes
from app.middleware.cors import setup_cors
from app.services.translation_service import translation_service
from app.services.conversion_service import conversion_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATHS = [
    Path("./translation_models/nllb-600m-ct2-int8"),
    Path("./translation_models/nllb-600m-ct2"),
    Path("./translation_models/nllb-600m"),
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    ram = psutil.virtual_memory()
    logger.info(f"RAM: {ram.total / (1024**3):.1f} GB total, {ram.available / (1024**3):.1f} GB available")

    model_path = None
    for path in MODEL_PATHS:
        if path.exists():
            logger.info(f"Found translation model: {path}")
            model_path = path
            break

    if model_path is None:
        logger.error(f"Translation model not found in: {MODEL_PATHS}")
    else:
        try:
            logger.info("Loading translation model...")
            translation_service.load_model(model_path, device="cpu")
            logger.info("Translation model ready")
        except Exception as e:
            logger.error(f"Translation load failed: {e}")
            traceback.print_exc()

    try:
        logger.info("Loading OCR model (EasyOCR)...")
        await asyncio.to_thread(conversion_service.load_model)
        logger.info("OCR model ready")
    except Exception as e:
        logger.error(f"OCR load failed: {e}")
        traceback.print_exc()

    yield # Сервер работает

    logger.info("Shutting down...")
    translation_service.unload()
    conversion_service.unload()


def create_app() -> FastAPI:
    application = FastAPI(
        title="MomsHelperBackend",
        lifespan=lifespan
    )

    setup_cors(application)
    setup_routes(application)

    return application

app = create_app()
