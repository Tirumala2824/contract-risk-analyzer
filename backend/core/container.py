from .database import db_manager
from ..repositories.document import MongoDocumentRepository
from ..repositories.analysis import MongoAnalysisRepository
from ..repositories.audit import MongoAuditRepository
from ..services.ingestion import IngestionService
from ..services.document_service import DocumentService
from ..services.orchestrator import OrchestrationService

class Container:
    """Dependency Injection Container."""
    
    def __init__(self):
        self.db_manager = db_manager
        
    async def init_resources(self):
        await self.db_manager.connect()
        self.db = self.db_manager.get_database()
        
        # Repositories
        self.document_repository = MongoDocumentRepository(self.db.documents)
        self.analysis_repository = MongoAnalysisRepository(self.db.analyses)
        self.audit_repository = MongoAuditRepository(self.db.audit_logs)
        
        # Services
        self.ingestion_service = IngestionService(self.document_repository)
        
        self.orchestration_service = OrchestrationService(
            self.analysis_repository,
            self.document_repository,
            self.audit_repository
        )
        
        self.document_service = DocumentService(
            self.ingestion_service,
            self.orchestration_service,
            self.document_repository,
            self.audit_repository
        )
        
    async def shutdown(self):
        await self.db_manager.disconnect()

# Global Container Instance
container = Container()
