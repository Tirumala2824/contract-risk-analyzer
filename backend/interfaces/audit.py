from abc import abstractmethod
from ..models import AuditLog
from .base import IRepository

class IAuditRepository(IRepository[AuditLog]):
    """Interface for audit log persistence."""
    pass
