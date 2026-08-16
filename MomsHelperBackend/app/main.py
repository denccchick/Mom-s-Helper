from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import traceback
import asyncio
from app.api.router import setup_routes
from app.middleware.cors import setup_cors
from app.services.translation_service import translation_service
from app.services.conversion_service import conversion_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Loading OCR model (EasyOCR)...")
        await asyncio.to_thread(conversion_service.load_model)
        logger.info("OCR model ready")
    except Exception as e:
        logger.error(f"OCR load failed: {e}")
        traceback.print_exc()

    try:
        logger.info("Loading translation model (NLLB)...")
        model_path = Path(__file__).parent.parent / "translation_models" / "nllb_ct2_int8_mom"
        await asyncio.to_thread(translation_service.load_model, model_path)
        logger.info("Translation model ready")
    except Exception as e:
        logger.error(f"Translation model load failed: {e}")
        traceback.print_exc()

    yield

    logger.info("Shutting down...")
    conversion_service.unload()
    translation_service.unload()

def create_app() -> FastAPI:
    application = FastAPI(
        title="MomsHelperBackend",
        lifespan=lifespan
    )

    setup_cors(application)
    setup_routes(application)

    return application

app = create_app()
