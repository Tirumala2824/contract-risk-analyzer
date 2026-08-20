from abc import abstractmethod
from typing import Optional
from ..models import AnalysisInDB, AnalysisStatus
from .base import IRepository

class IAnalysisRepository(IRepository[AnalysisInDB]):
    """Interface for analysis persistence."""

    @abstractmethod
    async def update_status(self, id: str, status: AnalysisStatus, error_message: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    async def update_results(self, id: str, results: dict) -> bool:
        pass
