from fastapi import FastAPI
from app.api.v1.endpoints.translation.router import router as translation_router
from app.api.v1.endpoints.system.health import router as health_router
from app.api.v1.endpoints.auth.user import router as user_router
from app.api.v1.endpoints.auth.role import router as role_router
from app.api.v1.endpoints.conversion.router import router as conversion_router   # добавлено

def setup_routes(app: FastAPI) -> None:
    app.include_router(user_router, prefix="/api/v1", tags=["auth"])
    app.include_router(role_router, prefix="/api/v1/roles", tags=["roles"])
    app.include_router(translation_router, prefix="/api/v1/translation", tags=["translation"])
    app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
    app.include_router(conversion_router, prefix="/api/v1/conversion", tags=["conversion"])   # добавлено
