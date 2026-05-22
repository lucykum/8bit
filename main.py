from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.compliance_engine import analyze_copy

app = FastAPI(title="GreenLight AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CopyRequest(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(req: CopyRequest):
    result = analyze_copy(req.text)
    return result

@app.get("/health")
async def health():
    return {"status": "ok"}