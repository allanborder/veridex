from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.ingestion.pipeline import ingestion_pipeline
from backend.config import settings

app = FastAPI(
    title="VERIDEX Core API",
    description="Self-Verifying Local AI Knowledge Assistant combining PS7 (Local RAG) with PS2 (NLI Verification)",
    version="1.0.0"
)

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
def on_startup():
    print("[VERIDEX] Initializing local knowledge base & vector index...")
    # Process any demo files present in data/documents
    ingestion_pipeline.process_directory(settings.data_dir)
    print("[VERIDEX] Ready on http://localhost:8000")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
