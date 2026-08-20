from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar, Any, Union, Dict

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    """Base interface for all repositories."""

    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        pass

    @abstractmethod
    async def list(self, limit: int = 100, skip: int = 0) -> List[T]:
        pass

    @abstractmethod
    async def add(self, entity: Union[T, Dict[str, Any]]) -> str:
        """Add entity and return its ID."""
        pass

    @abstractmethod
    async def update(self, id: str, entity: Union[T, Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass
