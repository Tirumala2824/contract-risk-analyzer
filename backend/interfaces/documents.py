from abc import abstractmethod
from typing import Optional, List
from ..models import DocumentInDB, DocumentStatus
from .base import IRepository

class IDocumentRepository(IRepository[DocumentInDB]):
    """Interface for document persistence."""

    @abstractmethod
    async def update_status(self, id: str, status: DocumentStatus, error_message: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    async def update_content(self, id: str, text: str, chunks: List[dict], metadata: Optional[dict]) -> bool:
        pass
