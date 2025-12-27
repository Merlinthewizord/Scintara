import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .archive import get_archive_item, read_archive, ensure_archive_dir
from .dialogue import run_archive_loop
from .settings import settings

logger = logging.getLogger("bloomed-terminal.server")

app = FastAPI(title="Bloomed Terminal", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _page(name: str) -> FileResponse:
    return FileResponse(STATIC_DIR / name)


@app.on_event("startup")
async def warmup():
    ensure_archive_dir()
    if settings.auto_archive:
        asyncio.create_task(run_archive_loop())


@app.get("/", include_in_schema=False)
def index():
    return _page("archive.html")


@app.get("/archive", include_in_schema=False)
def archive_page():
    return _page("archive.html")


@app.get("/archive/{entry_id}", include_in_schema=False)
def archive_detail(entry_id: str):
    return _page("conversation.html")


@app.get("/health")
def health():
    return {"ok": True}




@app.get("/v1/archive")
def archive(limit: int | None = None):
    return {"items": read_archive(limit=limit)}


@app.get("/v1/archive/{entry_id}")
def archive_item(entry_id: str):
    item = get_archive_item(entry_id)
    if item is None:
        return {"error": "Not found", "status": 404}
    return item


