import hashlib, json
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from app.config import settings
from app.models.domain import Investigation, InvestigationCreate
from app.core.pipeline import run_pipeline
from app.core.graph.builder import build_graph

router=APIRouter(prefix='/api/v1')
INVESTIGATIONS={}; RESULTS={}; UPLOAD_DIR=Path('investigations'); UPLOAD_DIR.mkdir(exist_ok=True)

def get_inv(i):
    inv=INVESTIGATIONS.get(i)
    if not inv: raise HTTPException(404,'Investigation not found.')
    return inv

@router.post('/investigations',response_model=Investigation,status_code=201)
async def create_investigation(subject_label:str=Form(...),context:str=Form(''),authorized:bool=Form(False),image:UploadFile|None=File(None)):
    if settings.require_authorization and not authorized: raise HTTPException(403,'Explicit authorization is required.')
    sha=None; name=None
    if image:
        data=await image.read()
        if len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,'Image exceeds upload limit.')
        sha=hashlib.sha256(data).hexdigest(); name=Path(image.filename or 'authorized-image').name
        (UPLOAD_DIR/f'{sha}_{name}').write_bytes(data)
    inv=Investigation(subject_label=subject_label.strip(),context=context.strip() or None,authorized=authorized,image_sha256=sha,image_name=name)
    INVESTIGATIONS[inv.id]=inv
    return inv

@router.post('/investigations/{investigation_id}/run')
async def run(investigation_id:UUID):
    inv=get_inv(investigation_id)
    if not inv.authorized: raise HTTPException(403,'Investigation is not authorized.')
    RESULTS[investigation_id]=run_pipeline(inv)
    return summarize(investigation_id)

@router.get('/investigations/{investigation_id}')
async def get(investigation_id:UUID):
    inv=get_inv(investigation_id); out={'investigation':inv.model_dump(mode='json'),'status':'ready' if investigation_id not in RESULTS else 'complete'}
    if investigation_id in RESULTS: out.update(summarize(investigation_id))
    return out

def summarize(i):
    d=RESULTS[i]; return {'investigation': INVESTIGATIONS[i].model_dump(mode='json'), 'resolution':d['resolution'].model_dump(mode='json'),'profiles':[p.model_dump(mode='json') for p in d['profiles']], 'conflicts':d['conflicts'],'timeline':d['timeline'],'evidence':[e.model_dump(mode='json') for e in d['candidate'].evidence],'graph':build_graph(d)}

@router.get('/investigations/{investigation_id}/report')
async def report(investigation_id:UUID):
    get_inv(investigation_id)
    if investigation_id not in RESULTS: raise HTTPException(409,'Run the investigation first.')
    return summarize(investigation_id)

@router.get('/investigations/{investigation_id}/report.html',response_class=HTMLResponse)
async def report_html(investigation_id:UUID):
    get_inv(investigation_id)
    if investigation_id not in RESULTS: raise HTTPException(409,'Run the investigation first.')
    d=summarize(investigation_id); inv=INVESTIGATIONS[investigation_id]
    rows=''.join(f"<tr><td>{p['platform']}</td><td>{p.get('username') or '—'}</td><td>{p.get('organization') or '—'}</td><td><a href='{p.get('url')}'>{p.get('url') or '—'}</a></td></tr>" for p in d['profiles'])
    ev=''.join(f"<li><b>{e['signal_type']}</b> — {e['claim']}<br><small>{e.get('source_url') or ''}</small></li>" for e in d['evidence'])
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>DigitalDNA Report</title><style>body{{font-family:Inter,Arial;background:#0b0d12;color:#e8eaf0;max-width:1100px;margin:40px auto;padding:0 24px}}section{{background:#131722;border:1px solid #272d3a;border-radius:16px;padding:20px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}td,th{{padding:10px;border-bottom:1px solid #272d3a;text-align:left}}a{{color:#8ab4ff}}.score{{font-size:42px;font-weight:800}}</style></head><body><h1>DigitalDNA Intelligence Report</h1><p>Authorized public-source investigation · {inv.subject_label}</p><section><div class='score'>{d['resolution']['score']:.0f}/100</div><b>{d['resolution']['status']}</b><p>Configured evidence resolution score, not a probability.</p></section><section><h2>Public profiles</h2><table><tr><th>Platform</th><th>Username</th><th>Organization</th><th>Source</th></tr>{rows}</table></section><section><h2>Evidence</h2><ul>{ev}</ul></section><section><h2>Conflicts</h2><pre>{json.dumps(d['conflicts'],indent=2)}</pre></section><section><h2>Timeline</h2><pre>{json.dumps(d['timeline'],indent=2)}</pre></section></body></html>"""
