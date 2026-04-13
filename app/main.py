from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.routers import api as api_router
from app.routers import meta as meta_router
from app.routers import public as public_router
from app.routers import auth_router

app = FastAPI(title="FilmDB", docs_url="/api/docs", redoc_url=None)

app.include_router(auth_router.router)
app.include_router(public_router.router)
app.include_router(api_router.router)
app.include_router(meta_router.router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── SPA routes ────────────────────────────────────────────────────────────────

@app.get("/admin", include_in_schema=False)
@app.get("/admin/{path:path}", include_in_schema=False)
def admin_spa(path: str = ""):
    return FileResponse(str(STATIC_DIR / "admin.html"))


@app.get("/", include_in_schema=False)
def main_spa():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/healthz")
def health():
    return {"status": "ok"}
