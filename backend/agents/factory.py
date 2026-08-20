from typing import List, Type
from ..models import RiskDomain
from .base import BaseRiskAgent
from .legal import LegalRiskAgent
from .compliance import ComplianceRiskAgent
from .financial import FinancialRiskAgent
from .operational import OperationalRiskAgent
from .security import SecurityRiskAgent
from .fraud import FraudRiskAgent

class AgentFactory:
    """Factory for creating risk analysis agents."""
    
    _agents = {
        RiskDomain.LEGAL: LegalRiskAgent,
        RiskDomain.COMPLIANCE: ComplianceRiskAgent,
        RiskDomain.FINANCIAL: FinancialRiskAgent,
        RiskDomain.OPERATIONAL: OperationalRiskAgent,
        RiskDomain.SECURITY: SecurityRiskAgent,
        RiskDomain.FRAUD: FraudRiskAgent
    }
    
    @classmethod
    def get_agent(cls, domain: RiskDomain) -> BaseRiskAgent:
        """Get agent instance for a domain."""
        agent_class = cls._agents.get(domain)
        if not agent_class:
            raise ValueError(f"Unknown risk domain: {domain}")
        return agent_class()
    
    @classmethod
    def get_all_agents(cls) -> List[BaseRiskAgent]:
        """Get all agent instances."""
        return [agent_class() for agent_class in cls._agents.values()]
