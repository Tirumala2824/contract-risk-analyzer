from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class SecurityRiskAgent(BaseRiskAgent):
    """Agent for Security Risk."""
    def __init__(self):
        super().__init__(RiskDomain.SECURITY)
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [{"name": "PII Exposure", "description": "Handling of names, emails"}, {"name": "Data Retention", "description": "Missing deletion policies"}]
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        return f"""Analyze for {parameter} risk. Context: {context}. 

Respond with a JSON object:
{{
    "detected": true/false,
    "finding": "Security/privacy risk identified",
    "evidence": "Relevant clause",
    "risk_level": "low/medium/high/critical",
    "explanation": "Security impact assessment",
    "recommendation": "Security control needed",
    "metadata": {{
        "has_pii": boolean,
        "protection_level": "none"|"weak"|"strong",
        "missing_retention_elements": integer,
        "required_retention_elements": integer (default 3),
        "has_encryption": boolean,
        "has_access_control": boolean,
        "has_certification": boolean,
        "has_notification_timeline": boolean,
        "has_accountability": boolean
    }}
}}

Focus on:
- PII Exposure: Strong protection = encryption + access control.
- Security: Encryption, certs (ISO 27001).
"""

    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        return []
