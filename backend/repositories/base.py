from typing import List, Optional, TypeVar, Generic, Any, Union, Dict
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from ..interfaces.base import IRepository

T = TypeVar('T')

class BaseMongoRepository(IRepository[T], Generic[T]):
    """Base MongoDB repository implementation."""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def get(self, id: str) -> Optional[T]:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(id)})
            return doc # Conversion to Model T should happen here or in service, usually mapping is good? 
                       # For now returning dict to be compatible with existing logic, or Pydantic model if we strictly type.
                       # Pydantic models are usually T.
        except Exception:
            return None

    async def list(self, limit: int = 100, skip: int = 0) -> List[T]:
        cursor = self.collection.find().skip(skip).limit(limit)
        results = []
        async for doc in cursor:
            # Map _id to id string if needed
            doc["id"] = str(doc.pop("_id"))
            results.append(doc)
        return results

    async def add(self, entity: Union[T, Dict[str, Any]]) -> str:
        # Entity is expected to be a dict or a model with .model_dump()
        # For simplicity, assuming dict or compatible
        if hasattr(entity, "model_dump"):
            data = entity.model_dump(by_alias=True, exclude_none=True)
        else:
            data = entity
            
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def update(self, id: str, entity: Union[T, Dict[str, Any]]) -> bool:
        if hasattr(entity, "model_dump"):
            data = entity.model_dump(exclude_unset=True)
        else:
            data = entity

        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    async def delete(self, id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
