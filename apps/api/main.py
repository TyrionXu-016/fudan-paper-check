from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.auth_routes import router as auth_router
from api.routes.papers import router as papers_router

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="Fudan Paper Pre-Check API", version="0.2.0")

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(papers_router)

if (WEB_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def index():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return {"message": "API running. Use Next.js frontend at http://localhost:3000"}
    return FileResponse(index_path)
