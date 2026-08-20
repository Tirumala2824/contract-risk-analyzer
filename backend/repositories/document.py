from typing import List, Optional
from bson import ObjectId
from ..interfaces.documents import IDocumentRepository
from ..models import DocumentStatus
from .base import BaseMongoRepository

class MongoDocumentRepository(BaseMongoRepository, IDocumentRepository):
    """MongoDB implementation of document repository."""

    async def update_status(self, id: str, status: DocumentStatus, error_message: Optional[str] = None) -> bool:
        update_data = {"status": status.value}
        if error_message:
            update_data["error_message"] = error_message
            
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def update_content(self, id: str, text: str, chunks: List[dict], metadata: Optional[dict]) -> bool:
        update_data = {
            "extracted_text": text,
            "chunks": chunks,
            "status": DocumentStatus.COMPLETED.value
        }
        if metadata:
            update_data["metadata"] = metadata
            
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
