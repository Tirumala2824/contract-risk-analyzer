from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class OperationalRiskAgent(BaseRiskAgent):
    """Agent for Operational Risk."""
    def __init__(self):
        super().__init__(RiskDomain.OPERATIONAL)
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [{"name": "Role Ambiguity", "description": "Unclear ownership"}, {"name": "SLA Risk", "description": "Undefined timelines"}]
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        return f"""Analyze for {parameter} risk. Context: {context}. 

Respond with a JSON object:
{{
    "detected": true/false,
    "finding": "Operational risk identified",
    "evidence": "Relevant section",
    "risk_level": "low/medium/high/critical",
    "explanation": "Operational impact assessment",
    "recommendation": "Process improvement needed",
    "metadata": {{
        "unassigned_roles": integer,
        "total_roles": integer (default 6),
        "missing_controls": integer,
        "required_controls": integer (default 8),
        "has_delivery_timeline": boolean,
        "has_response_sla": boolean,
        "has_uptime_guarantee": boolean,
        "unallocated_risks": integer,
        "total_risks": integer (default 2)
    }}
}}

Focus on:
- Roles: Named parties.
- Controls: Approval workflows.
- SLAs: Response/resolution times.
"""

    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        return []
