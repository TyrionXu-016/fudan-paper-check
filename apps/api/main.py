from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from api.auth_routes import router as auth_router
from api.exceptions import register_exception_handlers
from api.routes.check import router as check_router
from api.routes.decisions import router as decisions_router
from api.routes.export import router as export_router
from api.routes.papers import router as papers_router
from api.routes.progress import router as progress_router
from api.routes.result import router as result_router
from api.routes.rule_bases import router as rule_bases_router
from api.routes.tasks import router as tasks_router
from rag.rule_index import build_all_indexes

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    build_all_indexes()
    yield


app = FastAPI(title="Fudan Paper Pre-Check API", version="0.4.0", lifespan=lifespan)

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

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(papers_router)
app.include_router(rule_bases_router)
app.include_router(check_router)
app.include_router(tasks_router)
app.include_router(decisions_router)
app.include_router(export_router)
app.include_router(result_router)
app.include_router(progress_router)

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
