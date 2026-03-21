from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents, reviews

app = FastAPI(
    title="Tax Review API",
    description="AI-powered tax return and work paper review service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "api_key_configured": bool(settings.anthropic_api_key)}
