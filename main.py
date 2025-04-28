import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import logging
import os
import sys

from app.api import router
from app.config.config import settings
from app.db.database import create_db_and_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("semanticsql")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute startup code
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.APP_ENV} environment")
    try:
        logger.info("Initializing database...")
        await create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        if settings.APP_ENV == "production":
            logger.critical("Cannot start application without database")
            # In production, fail fast if database is not available
            sys.exit(1)
    yield
    # Execute shutdown code
    logger.info("Shutting down application...")

app = FastAPI(
    title="SemanticSQL API",
    description="Natural Language to SQL API using semantic search and LLMs",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Return a user-friendly error message
    error_detail = str(exc) if settings.APP_DEBUG else "An unexpected error occurred"
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "error": error_detail if settings.APP_DEBUG else None
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include API routes
app.include_router(router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        await create_db_and_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "name": settings.APP_NAME
        }
    )
