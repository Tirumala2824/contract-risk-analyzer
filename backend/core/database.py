from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from typing import Optional
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB connection manager."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        
    async def connect(self):
        """Connect to MongoDB."""
        settings = get_settings()
        
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_database]
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
            
            # Initialize indexes
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def _create_indexes(self):
        """Create database indexes."""
        if self.db is None:
            return

        # Documents collection indexes
        await self.db.documents.create_indexes([
            IndexModel([("upload_time", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("filename", ASCENDING)])
        ])
        
        # Analyses collection indexes
        await self.db.analyses.create_indexes([
            IndexModel([("document_id", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ])
        
        # Audit logs collection indexes
        await self.db.audit_logs.create_indexes([
            IndexModel([("document_id", ASCENDING)]),
            IndexModel([("analysis_id", ASCENDING)]),
            IndexModel([("timestamp", DESCENDING)])
        ])
        
        logger.info("Database indexes created")

    def get_database(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            raise RuntimeError("Database not initialized")
        return self.db

# Global instance for DI
db_manager = DatabaseManager()
