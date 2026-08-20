import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .core.container import container
from .routes import upload, analysis, audit # Updated import paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Contract Risk Analysis Platform...")
    
    # Initialize Container
    await container.init_resources()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await container.shutdown()

# Create FastAPI application
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-Agent AI Contract Risk Analysis Platform",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(audit.router)

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount static files
frontend_dir = BASE_DIR / "frontend"
if (frontend_dir / "static").exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")
if (frontend_dir / "css").exists():
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
if (frontend_dir / "js").exists():
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")

# Frontend Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    path = frontend_dir / "index.html"
    return FileResponse(path) if path.exists() else HTMLResponse("Frontend not found")

@app.get("/status/{id}", response_class=HTMLResponse)
async def status_page(id: str):
    path = frontend_dir / "status.html"
    return FileResponse(path) if path.exists() else HTMLResponse("Not found")

@app.get("/results/{id}", response_class=HTMLResponse)
async def results_page(id: str):
    path = frontend_dir / "results.html"
    return FileResponse(path) if path.exists() else HTMLResponse("Not found")

@app.get("/summary/{id}", response_class=HTMLResponse)
async def summary_page(id: str):
    path = frontend_dir / "summary.html"
    return FileResponse(path) if path.exists() else HTMLResponse("Not found")

@app.get("/history", response_class=HTMLResponse)
async def history_page():
    path = frontend_dir / "history.html"
    return FileResponse(path) if path.exists() else HTMLResponse("Not found")

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)