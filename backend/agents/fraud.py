from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class FraudRiskAgent(BaseRiskAgent):
    """Agent for Fraud Risk."""
    def __init__(self):
        super().__init__(RiskDomain.FRAUD)
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [{"name": "Document Tampering", "description": "Signs of altered sections"}, {"name": "Inconsistent Values", "description": "Conflicting dates/numbers"}]
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        return f"""Analyze for {parameter} risk. Context: {context}. 

Respond with a JSON object:
{{
    "detected": true/false,
    "finding": "Anomaly identified",
    "evidence": "Suspicious content",
    "risk_level": "low/medium/high/critical",
    "explanation": "Why this is suspicious",
    "recommendation": "Verification needed",
    "metadata": {{
        "tampering_anomaly_score": float (0.0-1.0),
        "language_anomaly_index": float (0.0-1.0),
        "conflicting_fields": integer,
        "critical_fields": integer (default 4),
        "duplication_severity": float (0.0-1.0)
    }}
}}

Focus on:
- Fraud indicators.
"""

    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        return []
