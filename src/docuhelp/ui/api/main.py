"""
Main FastAPI application for Surgical Report Generator
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from .routes import video, feedback, report
from ..firebase_config import initialize_firebase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    logger.info("Starting Surgical Report Generator API...")

    # Firebase is optional - only initialize if enabled
    # use_firebase = os.getenv("USE_FIREBASE", "false").lower() == "true"
    # if use_firebase:
    #     try:
    #         initialize_firebase()
    #         logger.info("Firebase initialized successfully")
    #     except Exception as e:
    #         logger.warning(f"Firebase initialization failed: {e}")
    #         logger.info("Running in local-only mode")
    # else:
    logger.info("Running in local-only mode (Firebase disabled)")

    yield

    # Shutdown
    logger.info("Shutting down API...")


# Initialize FastAPI app
app = FastAPI(
    title="Surgical Report Generator API",
    description="AI-powered surgical video analysis and report generation",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(video.router, prefix="/api/v1/video", tags=["video"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(report.router, prefix="/api/v1/report", tags=["report"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Surgical Report Generator API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
