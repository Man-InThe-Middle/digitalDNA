from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from app.config import settings
from app.api.routes import router
app=FastAPI(title='DigitalDNA',version='1.0.0',description='Evidence-driven public identity intelligence.')
app.include_router(router)
@app.get('/health')
async def health(): return {'status':'ok','service':'DigitalDNA','version':'1.0.0'}
@app.get('/')
async def dashboard(): return FileResponse(Path(__file__).parent/'static'/'index.html')
