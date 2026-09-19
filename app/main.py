from fastapi import FastAPI
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Evidence-driven public identity and digital footprint intelligence.",
)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "DigitalDNA", "version": "0.1.0"}
