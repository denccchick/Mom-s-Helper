from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import traceback
import asyncio
import sys
from app.api.router import setup_routes
from app.middleware.cors import setup_cors
from app.services.translation_service import translation_service
from app.services.conversion_service import conversion_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "translation_models" / "nllb_ct2_int8_mom"

logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"MODEL_PATH: {MODEL_PATH}")
logger.info(f"MODEL_PATH exists: {MODEL_PATH.exists()}")

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
        logger.info(f"Loading model from: {MODEL_PATH}")
        await asyncio.to_thread(translation_service.load_model, MODEL_PATH)
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

if __name__ == "__main__":
    import uvicorn
    import multiprocessing

    multiprocessing.freeze_support()

    print("Starting Uvicorn server from EXE...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
