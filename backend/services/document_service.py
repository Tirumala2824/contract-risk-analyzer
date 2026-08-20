import logging
import datetime
from typing import Optional, List
from fastapi import UploadFile, HTTPException, BackgroundTasks
from ..models import (
    UploadResponse, DocumentResponse, FileType, 
    AnalysisMode, AuditLogAction, DocumentStatus
)
from ..interfaces.services import IDocumentService, IIngestionService, IOrchestrationService
from ..interfaces.documents import IDocumentRepository
from ..interfaces.audit import IAuditRepository

logger = logging.getLogger(__name__)

class DocumentService(IDocumentService):
    """Service for handling document business logic."""
    
    def __init__(
        self,
        ingestion_service: IIngestionService,
        orchestration_service: IOrchestrationService, # Circular dep potential? Only interface needed
        document_repository: IDocumentRepository,
        audit_repository: IAuditRepository,
        background_tasks: BackgroundTasks = None
    ):
        self.ingestion_service = ingestion_service
        self.orchestration_service = orchestration_service
        self.document_repository = document_repository
        self.audit_repository = audit_repository
        self.background_tasks = background_tasks

    def set_background_tasks(self, tasks: BackgroundTasks):
        self.background_tasks = tasks

    async def upload_document(
        self, 
        file: UploadFile, 
        mode: AnalysisMode, 
        reference_file: Optional[UploadFile] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> UploadResponse:
        try:
            # 1. Read and Validate Main File
            content = await file.read()
            filename = file.filename or "unknown"
            
            is_valid, msg = self.ingestion_service.validate_file(filename, len(content))
            if not is_valid:
                raise HTTPException(status_code=400, detail=msg)
                
            # 2. Save File
            unique_filename, file_path = await self.ingestion_service.save_file(filename, content)
            
            # 3. Create Document Record
            ext = filename.rsplit(".", 1)[-1].lower()
            doc_data = {
                "filename": unique_filename,
                "original_name": filename,
                "file_type": FileType(ext).value,
                "file_path": file_path,
                "upload_time": datetime.datetime.utcnow(),
                "status": DocumentStatus.UPLOADED.value,
                "extracted_text": None,
                "chunks": []
            }
            document_id = await self.document_repository.add(doc_data)
            
            # 4. Log Audit
            await self.audit_repository.add({
                "document_id": document_id,
                "action": AuditLogAction.DOCUMENT_UPLOADED.value,
                "timestamp": datetime.datetime.utcnow(),
                "details": {
                    "original_name": filename,
                    "size_bytes": len(content)
                }
            })
            
            # 5. Handle Reference File
            reference_document_id = None
            if reference_file:
                ref_content = await reference_file.read()
                ref_filename = reference_file.filename or "reference"
                ref_valid, _ = self.ingestion_service.validate_file(ref_filename, len(ref_content))
                if ref_valid:
                    ref_unique, ref_path = await self.ingestion_service.save_file(ref_filename, ref_content)
                    
                    ref_data = {
                        "filename": ref_unique,
                        "original_name": ref_filename,
                        "file_type": FileType(ref_filename.rsplit(".", 1)[-1].lower()).value,
                        "file_path": ref_path,
                        "upload_time": datetime.datetime.utcnow(),
                        "status": DocumentStatus.UPLOADED.value
                    }
                    reference_document_id = await self.document_repository.add(ref_data)

            # 6. Create Analysis
            analysis_id = await self.orchestration_service.create_analysis(
                document_id, mode, reference_document_id
            )
            
            # 7. Start Background Processing
            if background_tasks:
                background_tasks.add_task(
                    self._process_and_analyze, 
                    document_id, 
                    analysis_id, 
                    reference_document_id
                )
            else:
                 # Fallback if no tasks provided: run immediately? Or log warning.
                 # For async consistency, better to warn. But for now, let's just log.
                 logger.warning("No background_tasks provided. Analysis will not run automatically.")
            
            return UploadResponse(
                success=True,
                message="Document uploaded successfully. Analysis started.",
                document_id=document_id,
                analysis_id=analysis_id
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _process_and_analyze(self, document_id: str, analysis_id: str, ref_id: Optional[str]):
        """Background task logic."""
        try:
            # Extract Main
            success = await self.ingestion_service.extract_text(document_id)
            if not success:
               logger.error(f"Extraction failed for {document_id}")
               return

            # Log
            await self.audit_repository.add({
                "document_id": document_id,
                "analysis_id": analysis_id,
                "action": AuditLogAction.DOCUMENT_PROCESSED.value,
                "timestamp": datetime.datetime.utcnow(),
                "details": {"status": "Text extraction completed"}
            })
            
            # Extract Ref
            if ref_id:
                await self.ingestion_service.extract_text(ref_id)
                
            # Run Analysis
            await self.orchestration_service.run_analysis(analysis_id)
            
        except Exception as e:
            logger.error(f"Background process failed: {e}")

    async def get_document(self, document_id: str) -> DocumentResponse:
        doc = await self.document_repository.get(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        return DocumentResponse(
            id=str(doc.get("_id") or doc.get("id")),
            filename=doc["filename"],
            original_name=doc["original_name"],
            file_type=doc["file_type"],
            upload_time=doc["upload_time"],
            status=doc["status"],
            metadata=doc.get("metadata")
        )

    async def list_documents(self, limit: int = 20, skip: int = 0) -> dict:
        docs = await self.document_repository.list(limit, skip)
        results = []
        for doc in docs:
            results.append({
                "id": str(doc.get("_id") or doc.get("id")),
                "original_name": doc["original_name"],
                "file_type": doc["file_type"],
                "upload_time": doc["upload_time"],
                "status": doc["status"]
            })
        return {"documents": results, "count": len(results)}
