"""RepoPilot API entry point.  Run:  uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import assistant_routes, issue_routes, onboarding_routes, repository_routes
from app.config import settings
from app.errors import AppError
from app.llm import ollama_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("repopilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    logger.info("RepoPilot started. Ollama model: %s @ %s", settings.OLLAMA_MODEL, settings.OLLAMA_BASE_URL)
    yield


app = FastAPI(
    title="RepoPilot API",
    description="Agentic AI system for automated repository understanding and developer onboarding.",
    version="1.0.0", lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    print("REPOPILOT ERROR:", repr(exc))
    logger.error("%s %s -> %s: %s", request.method, request.url.path, exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.middleware("http")
async def catch_unexpected_errors(request: Request, call_next):
    """Last line of defence: log the real exception, never leak a stack trace to the client."""
    try:
        return await call_next(request)
    except Exception as exc:
        print("REPOPILOT ERROR:", repr(exc))
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error. Check backend logs.",
                                                      "code": "internal_error"})


# Added last so it is the outermost middleware (CORS headers are also present on error responses).
app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(repository_routes.router)
app.include_router(assistant_routes.router)
app.include_router(onboarding_routes.router)
app.include_router(issue_routes.router)


@app.get("/", tags=["system"])
def root():
    return {"name": "RepoPilot", "version": "1.0.0", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "ollama": ollama_client.check_status(), "embedding_model": settings.EMBEDDING_MODEL}
