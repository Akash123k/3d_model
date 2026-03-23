"""
FastAPI Application - Main Entry Point
STEP CAD Viewer Backend API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import structlog

from app.config import settings
from app.core.logging import log, access_log
from app.core.exceptions import (
    STEPProcessingError,
    FileUploadError,
    ModelNotFoundError,
    GeometryExtractionError,
    InvalidFileFormatError,
    FileSizeLimitError
)
from app.api.routes import upload, model
from app.db.database import init_db, check_db_connection

# Initialize FastAPI app
app = FastAPI(
    title="STEP CAD Viewer API",
    description="Backend API for STEP file visualization and analysis",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    log.info("application_startup", status="database_initialization")
    try:
        init_db()
        if check_db_connection():
            log.info("database_connection_verified", status="success")
        else:
            log.warning("database_connection_failed", status="error")
    except Exception as e:
        log.error("database_initialization_error", error=str(e))


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    log.error("unhandled_exception",
             path=str(request.url.path),
             method=request.method,
             error=str(exc),
             error_type=type(exc).__name__)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


# Custom exception handlers
@app.exception_handler(STEPProcessingError)
@app.exception_handler(FileUploadError)
@app.exception_handler(ModelNotFoundError)
@app.exception_handler(GeometryExtractionError)
@app.exception_handler(InvalidFileFormatError)
@app.exception_handler(FileSizeLimitError)
async def custom_exception_handler(request: Request, exc):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


# Middleware for logging requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    access_log.info("http_request_started",
                   method=request.method,
                   path=request.url.path,
                   client_ip=request.client.host if request.client else "unknown")
    
    response = await call_next(request)
    
    access_log.info("http_request_completed",
                   method=request.method,
                   path=request.url.path,
                   status_code=response.status_code)
    
    return response


# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(model.router, prefix="/api")


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "STEP CAD Viewer API",
        "version": "1.0.0",
        "description": "Backend API for STEP file visualization and analysis",
        "documentation": "/api/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
