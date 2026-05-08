"""
Main FastAPI application for the distributed task queue system.
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from src.config import config
from src.utils import setup_logging
from src.db import init_db
from src.api import router

# Setup logging
logger = setup_logging(__name__, level=config.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan.
    Opens database connection when the app starts,
    closes it when the app stops.
    """
    logger.info("Starting FastAPI application")
    init_db()
    yield
    logger.info("Shutting down FastAPI application")


# Create FastAPI app
app = FastAPI(
    title="Distributed Task Queue System",
    description="A production-grade distributed task queue using FastAPI and Redis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the UI Dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(router)


@app.get("/", tags=["root"], include_in_schema=False)
def read_root():
    """Root endpoint servers the UI Dashboard."""
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {config.api.host}:{config.api.port}")
    
    uvicorn.run(
        app,
        host=config.api.host,
        port=config.api.port,
        workers=config.api.workers,
        log_level=config.log_level.lower(),
    )
