# Routes package
from .upload import router as upload_router
from .analysis import router as analysis_router
from .audit import router as audit_router

__all__ = ["upload_router", "analysis_router", "audit_router"]
