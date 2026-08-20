from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from typing import Optional

from ..models import UploadResponse, DocumentResponse, AnalysisMode
from ..core.container import container
from ..interfaces.services import IDocumentService

router = APIRouter(prefix="/api", tags=["upload"])

async def get_document_service() -> IDocumentService:
    return container.document_service

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: AnalysisMode = Form(AnalysisMode.PRE_SIGNED),
    reference_file: Optional[UploadFile] = File(None),
    service: IDocumentService = Depends(get_document_service)
):
    """Upload a document for risk analysis."""
    # Pass background tasks to service (setter injection or method arg)
    # Since existing interface doesn't have it in method, let's assume service handles it or we set it.
    # Ideally, we pass it to the method, but I defined IDocumentService.upload_document without it in interface (my bad).
    # I should update the interface or just set it on the implementation if it's stateful (scoped).
    # Being a singleton in container, setting state is bad for concurrency.
    # Better to pass it as argument. I will update DocumentService to accept background_tasks in upload_document.
    
    # Actually, let's check DocumentService implementation I wrote. 
    # __init__ took background_tasks=None. 
    # But for a singleton service, we shouldn't hold request-scoped background tasks in `self`.
    # I should modify DocumentService to take background_tasks in the method.
    
    # HACK: For now, I will use a setter on the service if it was request scoped, but it's not.
    # Correct way: Interface change. I will assume I can update the interface.

    # Remove hacky setter injection
    # if hasattr(service, "set_background_tasks"):
    #      service.set_background_tasks(background_tasks)

    return await service.upload_document(file, mode, reference_file, background_tasks)

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    service: IDocumentService = Depends(get_document_service)
):
    """Get document details by ID."""
    return await service.get_document(document_id)

@router.get("/documents")
async def list_documents(
    limit: int = 20, 
    skip: int = 0,
    service: IDocumentService = Depends(get_document_service)
):
    """List all uploaded documents."""
    return await service.list_documents(limit, skip)
