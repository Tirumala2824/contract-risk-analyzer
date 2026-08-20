from typing import Optional
from datetime import datetime
from bson import ObjectId
from ..interfaces.analysis import IAnalysisRepository
from ..models import AnalysisStatus
from .base import BaseMongoRepository

class MongoAnalysisRepository(BaseMongoRepository, IAnalysisRepository):
    """MongoDB implementation of analysis repository."""

    async def update_status(self, id: str, status: AnalysisStatus, error_message: Optional[str] = None) -> bool:
        update_data = {"status": status.value}
        if status == AnalysisStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
        if error_message:
            update_data["error_message"] = error_message
            
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def update_results(self, id: str, results: dict) -> bool:
        # Expecting results to contain scores, summary, etc.
        results["completed_at"] = datetime.utcnow()
        results["status"] = AnalysisStatus.COMPLETED.value
        
        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": results}
        )
        return result.modified_count > 0
