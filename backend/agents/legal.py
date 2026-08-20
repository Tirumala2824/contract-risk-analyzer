from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class LegalRiskAgent(BaseRiskAgent):
    """Agent for Legal & Contractual Risk analysis."""
    
    def __init__(self):
        super().__init__(RiskDomain.LEGAL)
    
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [
            {"name": "Ambiguous Clauses", "description": "Vague terms like 'as applicable', 'reasonable efforts', 'best efforts'"},
            {"name": "Missing Obligations", "description": "Absence of SLAs, penalties, or performance guarantees"},
            {"name": "Liability Exposure", "description": "Unlimited or uncapped liability clauses"},
            {"name": "Termination Risk", "description": "One-sided termination rights or short notice periods"},
            {"name": "Jurisdiction Mismatch", "description": "Unfavorable governing law or dispute resolution venues"}
        ]
    
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        return f"""Analyze the following contract text for "{parameter}" risk.
CONTRACT TEXT:
{context}

Respond with a JSON object containing:
{{
    "detected": true/false,
    "finding": "What was found or not found",
    "evidence": "Direct quote from text if found",
    "risk_level": "low/medium/high/critical",
    "explanation": "Why this risk level",
    "recommendation": "Suggested action",
    "metadata": {{
        "ambiguous_count": integer (number of ambiguous phrases found),
        "missing_count": integer (number of missing obligations),
        "expected_count": integer (default 8),
        "cap_type": "unlimited"|"no_cap"|"worse"|"equal"|"better",
        "cap_amount": number (liability cap value if found, else 0),
        "asymmetry": boolean (is termination one-sided?),
        "no_cure": boolean (is cure period missing?),
        "no_notice": boolean (is notice period < 30 days?),
        "notice_days": integer (notice period in days),
        "mismatch_type": "different_country"|"different_venue"|"aligned"
    }}
}}

Focus on:
- Ambiguous Clauses: Count phrases like "as applicable", "reasonable efforts", "best efforts".
- Missing Obligations: Check for SLA definitions, penalty clauses.
- Liability: Check cap amount vs contract value.
- Termination: Check notice days and cure periods.
- Jurisdiction: Check governing law and venue.
"""
    
    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        keywords = {
            "Ambiguous Clauses": ["as applicable", "reasonable efforts", "best efforts", "may include"],
            "Missing Obligations": ["sla", "service level", "penalty", "damages", "guarantee"],
            "Liability Exposure": ["unlimited liability", "liability cap", "indemnify", "hold harmless"],
            "Termination Risk": ["terminate", "termination", "notice period", "for convenience"],
            "Jurisdiction Mismatch": ["governing law", "jurisdiction", "dispute resolution", "arbitration"]
        }
        return keywords.get(param_name, [])
