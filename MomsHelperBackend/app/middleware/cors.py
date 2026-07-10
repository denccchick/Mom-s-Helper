import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    load_dotenv()
    origins_str = os.getenv("ALLOWED_ORIGINS", "")

    if origins_str:
        allowed_origins = [origin.strip() for origin in origins_str.split(",")]
    else:
        allowed_origins = []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
