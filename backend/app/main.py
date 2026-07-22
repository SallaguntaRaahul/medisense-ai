from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Database
from app.graph import build_graph
from app.ingestion import build_documents, load_or_fetch_corpus
from app.models import ChatRequest, ChatResponse, HealthResponse, SourceChunk, TriagePrediction
from app.security import get_rate_limiter
from app.triage_classifier import get_triage_classifier
from app.vector_store import build_or_load_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("medisense")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Database(settings.db_path)

    topics = load_or_fetch_corpus(settings.medlineplus_cache_path)
    documents = build_documents(topics, settings.chunk_size, settings.chunk_overlap)
    vector_store = build_or_load_vector_store(settings.vector_index_path, settings.embedding_model, documents=documents)

    triage_classifier = get_triage_classifier(settings.triage_adapter_path, settings.triage_base_model)

    app.state.graph = build_graph(settings, vector_store, triage_classifier)
    logger.info("MediSense ready: %d topics, %d chunks indexed", len(topics), len(documents))
    yield


app = FastAPI(title="MediSense AI", description="Medical RAG chatbot (portfolio demo, not a clinical tool)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db(request: Request) -> Database:
    return request.app.state.db


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request, db: Database = Depends(get_db)):
    client_id = request.client.host if request.client else "unknown"
    if not get_rate_limiter().check(client_id):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "rate limit exceeded, try again shortly")

    session_id = db.ensure_session(payload.session_id)

    result = request.app.state.graph.invoke({"question": payload.message})

    db.add_message(session_id, "user", payload.message)
    db.add_message(session_id, "assistant", result["answer"])

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=[SourceChunk(**s) for s in result.get("sources", [])],
        triage=TriagePrediction(label=result["triage_label"], confidence=result["triage_confidence"]),
        guardrail_rewritten=result.get("guardrail_rewritten", False),
        injection_flagged=result.get("injection_flagged", False),
    )


@app.get("/api/chat/{session_id}/history")
async def chat_history(session_id: str, db: Database = Depends(get_db)):
    return db.get_history(session_id)
