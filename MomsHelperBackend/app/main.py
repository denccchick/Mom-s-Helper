from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from app.api.router import setup_routes
from app.middleware.cors import setup_cors
from app.services.translation_service import translation_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_PATH = Path("./models/nllb-600m-ct2")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_PATH.exists():
        logger.info("Loading translation model...")
        try:
            translation_service.load_model(MODEL_PATH, device="cpu")
            logger.info("Translation model ready")
        except Exception as e:
            logger.error(f"Failed to load translation model: {e}")
    else:
        logger.warning(f"Model not found at {MODEL_PATH}")

    yield

    logger.info("Shutting down...")
    translation_service.unload()


def create_app() -> FastAPI:
    application = FastAPI(
        title="ControlChartsBackend",
        lifespan=lifespan
    )

    setup_cors(application)
    setup_routes(application)

    return application


app = create_app()
