from fastapi import APIRouter
from datetime import datetime, UTC
import os

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": os.getenv("SERVICE_NAME", "fastapi-server")
    }
