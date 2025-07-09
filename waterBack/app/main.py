import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings, openrouter_config
from app.models.responses import HealthResponse, ApiError


# Create necessary directories
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    directories = [
        settings.UPLOAD_FOLDER,
        settings.TEMP_FOLDER,
        settings.REPORTS_FOLDER,
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    if settings.DEBUG_MODE:
        print("🚀 [Startup] Water Test Analyzer Backend")
        print(f"   📁 Created directories: {', '.join(directories)}")
        print(f"   🌐 CORS origins: {settings.CORS_ORIGINS}")
        print(f"   🤖 AI Model: {openrouter_config.get_model_name(openrouter_config.DEFAULT_MODEL)}")
    
    yield
    
    # Shutdown
    if settings.DEBUG_MODE:
        print("👋 [Shutdown] Water Test Analyzer Backend")

# Initialize FastAPI
app = FastAPI(
    title="Water Test Analyzer API",
    description="AI-powered water quality test analysis system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    if settings.DEBUG_MODE:
        print(f"❌ [Error] {exc}")
    
    return JSONResponse(
        status_code=500,
        content=ApiError(
            message="Internal server error",
            status=500,
            code="INTERNAL_ERROR"
        ).dict()
    )

# Health check endpoint
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=int(time.time())
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Water Test Analyzer API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# Include API routers
from app.api import upload, analysis, streaming

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(streaming.router, prefix="/api", tags=["Streaming"])

if __name__ == "__main__":
    import uvicorn
    
    if settings.DEBUG_MODE:
        print(f"🌐 [Server] Starting on {settings.APP_HOST}:{settings.APP_PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG_MODE,
        log_level="debug" if settings.DEBUG_MODE else "info"
    ) 