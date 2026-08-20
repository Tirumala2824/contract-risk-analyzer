from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ...models import RiskFinding, RiskLevel, JudgeScore

class RiskCategoryScorer(ABC):
    """Abstract base class for deterministic category scoring."""
    
    @abstractmethod
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        """Calculate the deterministic base score from findings metadata."""
        pass

class ConsensusJudge(ABC):
    """Abstract base class for a consensus judge."""
    
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def evaluate(self, base_score: float, findings: List[RiskFinding], context: Dict[str, Any]) -> float:
        """Evaluate and refine the score. Returns a score between 0-100."""
        pass
