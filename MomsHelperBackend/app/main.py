from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import psutil

from app.api.router import setup_routes
from app.middleware.cors import setup_cors
from app.services.translation_service import translation_service

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
            logger.info(f"Found model: {path}")
            model_path = path
            break

    if model_path is None:
        logger.error(f"Model not found in: {MODEL_PATHS}")
        yield
        return

    try:
        logger.info("Loading model...")
        translation_service.load_model(model_path, device="cpu")
        logger.info("✅ Model ready")
    except Exception as e:
        logger.error(f"❌ Load failed: {e}")
        import traceback
        traceback.print_exc()

    yield

    logger.info("Shutting down...")
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
