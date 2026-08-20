from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict
from fastapi import UploadFile, BackgroundTasks
from ..models import AnalysisMode, FileType, UploadResponse, DocumentResponse, AnalysisStatus, DocumentStatus

class IIngestionService(ABC):
    """Interface for ingestion service."""
    
    @abstractmethod
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        pass
        
    @abstractmethod
    async def save_file(self, filename: str, content: bytes) -> Tuple[str, str]:
        pass
        
    @abstractmethod
    async def extract_text(self, document_id: str) -> bool:
        pass

class IDocumentService(ABC):
    """Interface for document service."""
    
    @abstractmethod
    async def upload_document(
        self, 
        file: UploadFile, 
        mode: AnalysisMode, 
        reference_file: Optional[UploadFile] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> UploadResponse:
        pass
        
    @abstractmethod
    async def get_document(self, document_id: str) -> DocumentResponse:
        pass
        
    @abstractmethod
    async def list_documents(self, limit: int = 20, skip: int = 0) -> dict:
        pass

class IOrchestrationService(ABC):
    """Interface for orchestration service."""
    
    @abstractmethod
    async def create_analysis(
        self, 
        document_id: str, 
        mode: AnalysisMode, 
        reference_document_id: Optional[str] = None
    ) -> str:
        pass
        
    @abstractmethod
    async def run_analysis(self, analysis_id: str) -> bool:
        pass
        
    @abstractmethod
    async def get_analysis_status(self, analysis_id: str) -> Optional[dict]:
        pass
        
    @abstractmethod
    async def get_analysis_results(self, analysis_id: str) -> Optional[dict]:
        pass
    
    @abstractmethod
    async def list_analyses(self, limit: int = 50, skip: int = 0) -> list:
        """List all analyses for history."""
        pass

class IAnalysisService(ABC):
    """Interface for analysis aggregation logic (if separate)."""
    pass
