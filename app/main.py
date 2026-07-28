from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_health import router as health_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title=settings.app_name)
app.include_router(health_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def serve_chat_interface() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
