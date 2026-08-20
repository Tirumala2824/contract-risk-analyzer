from .base import BaseMongoRepository
from ..interfaces.audit import IAuditRepository

class MongoAuditRepository(BaseMongoRepository, IAuditRepository):
    """MongoDB implementation of audit repository."""
    pass
