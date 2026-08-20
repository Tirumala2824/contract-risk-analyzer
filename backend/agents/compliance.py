from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class ComplianceRiskAgent(BaseRiskAgent):
    """Agent for Compliance & Regulatory Risk analysis."""
    def __init__(self):
        super().__init__(RiskDomain.COMPLIANCE)
    
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [
            {"name": "Policy Violations", "description": "Missing mandatory clauses or standard requirements"},
            {"name": "Regulatory Gaps", "description": "GDPR, HIPAA, SOX, or industry-specific compliance gaps"},
            {"name": "Audit Readiness", "description": "Missing approval trails or audit provisions"}
        ]
    
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        return f"""Analyze the following contract for "{parameter}" compliance risk.
CONTRACT TEXT:
{context}

Respond with a JSON object:
{{
    "detected": true/false,
    "finding": "Description of compliance issue or confirmation",
    "evidence": "Relevant text excerpt",
    "risk_level": "low/medium/high/critical",
    "explanation": "Compliance assessment rationale",
    "recommendation": "Required actions",
    "metadata": {{
        "missing_mandatory": integer (count of missing policies),
        "total_mandatory": integer (default 5),
        "missing_regs": integer (count of missing regulations),
        "applicable_regs": integer (default 4),
        "missing_reg_names": [list of missing regs],
        "mentioned_gdpr": boolean,
        "has_approval_workflow": boolean,
        "has_audit_trail": boolean,
        "has_responsible_party": boolean,
        "similarity_score": float (0.0-1.0, default 1.0 if standard)
    }}
}}

Focus on:
- GDPR: Data processing, consent, data subject rights.
- Audit provisions: Right to audit, record keeping.
"""

    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        # Basic keyword fallback
        return []
