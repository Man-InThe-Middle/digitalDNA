from __future__ import annotations
import json
import re
import httpx
from app.models.domain import Candidate, Evidence, ProfileRecord

SYSTEM = """You are a public-source identity intelligence analyst. Use ONLY the supplied public evidence. Do not invent facts, private data, credentials, or biometric conclusions. Return JSON with keys: summary (string), corroborated_claims (array of strings), contradictions (array of strings), next_checks (array of strings)."""

class OllamaAnalyzer:
    name="ollama_local"
    def __init__(self,url="http://127.0.0.1:11434",model="qwen3:8b",timeout=45.0): self.url=url.rstrip('/'); self.model=model; self.timeout=timeout
    async def analyze(self, subject: str, candidate: Candidate, evidence: list[Evidence]) -> dict:
        payload={"subject":subject,"profiles":[p.model_dump(mode="json") for p in candidate.profiles],"evidence":[e.model_dump(mode="json") for e in evidence]}
        prompt=SYSTEM+"\nINPUT:\n"+json.dumps(payload,ensure_ascii=False)[:30000]
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r=await client.post(f"{self.url}/api/chat",json={"model":self.model,"stream":False,"format":"json","messages":[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}]})
            r.raise_for_status(); data=r.json(); content=data.get("message",{}).get("content","")
        try: return json.loads(content)
        except json.JSONDecodeError:
            match=re.search(r"\{.*\}",content,re.S)
            if match: return json.loads(match.group(0))
            return {"summary":content,"corroborated_claims":[],"contradictions":[],"next_checks":[]}
