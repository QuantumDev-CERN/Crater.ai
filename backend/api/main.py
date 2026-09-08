"""FastAPI app entrypoint. Run with: uvicorn backend.api.main:app --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.routes import ingestion, products, query
from backend.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Crater.ai — Phase 1: Product Knowledge", version="0.1.0", lifespan=lifespan)

app.include_router(products.router)
app.include_router(ingestion.router)
app.include_router(query.router)


@app.get("/health")
def health():
    return {"status": "ok"}
