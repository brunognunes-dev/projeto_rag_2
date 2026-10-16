import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.services.ocr_ingestion import ingestion_service
from src.services.rag_service import rag_service
from src.core.config import config

app = FastAPI(title="RAG + Bruno Gabriel Nunes", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    files: list[str] = []

class QueryRequest(BaseModel):
    question: str

@app.get("/api/status")
def get_status():
    has_supabase = bool(config.SUPABASE_URL and config.SUPABASE_KEY)
    has_openrouter = bool(config.OPENROUTER_API_KEY)
    return {
        "app": "RAG + Bruno Gabriel Nunes",
        "supabase_connected": has_supabase,
        "openrouter_configured": has_openrouter,
        "embedding_model": config.EMBEDDING_MODEL_NAME,
        "llm_model": config.OPENROUTER_MODEL
    }

@app.get("/api/documents")
def list_documents():
    docs = ingestion_service.list_available_documents()
    return {"documents": docs}

@app.post("/api/ingest")
def run_ingestion(req: IngestRequest):
    try:
        res = ingestion_service.run_ingestion_pipeline(req.files)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante ingestão: {str(e)}")

@app.post("/api/query")
def run_query(req: QueryRequest):
    try:
        res = rag_service.query(req.question)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro durante consulta: {str(e)}")

# Serve static directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
