"""
MongoDB database connection and utilities.
Provides async database operations using Motor.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, DESCENDING
from typing import Optional
import logging

from .config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self):
        """Connect to MongoDB and create indexes."""
        settings = get_settings()
        
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_database]
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
            
            # Create indexes
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
        """Create database indexes for optimal performance."""
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
    
    # Collection accessors
    @property
    def documents(self):
        """Get documents collection."""
        return self.db.documents
    
    @property
    def analyses(self):
        """Get analyses collection."""
        return self.db.analyses
    
    @property
    def audit_logs(self):
        """Get audit_logs collection."""
        return self.db.audit_logs


# Global database instance
database = Database()


async def get_database() -> Database:
    """Dependency injection for database access."""
    return database
