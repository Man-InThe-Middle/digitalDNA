from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title="DigitalDNA",
    version="2.1.0",
    description="Evidence-driven public identity intelligence.",
)
app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "2.1.0",
        "persistence": "sqlite",
        "public_sources_only": settings.public_sources_only,
    }


@app.get("/")
async def dashboard():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
