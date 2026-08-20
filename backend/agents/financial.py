from typing import List, Dict
from ..models import RiskDomain
from .base import BaseRiskAgent

class FinancialRiskAgent(BaseRiskAgent):
    """Agent for Financial Risk analysis."""
    def __init__(self):
        super().__init__(RiskDomain.FINANCIAL)
    
    @property
    def parameters(self) -> List[Dict[str, str]]:
        return [
            {"name": "Payment Terms", "description": "Long credit cycles, unclear payment schedules"},
            {"name": "Penalty Clauses", "description": "Excessive fines or liquidated damages"},
            {"name": "Revenue Leakage", "description": "Missing escalation or price revision clauses"}
        ]

    def get_analysis_prompt(self, parameter: str, context: str) -> str:
         return f"""Analyze the following contract for "{parameter}" financial risk.
CONTRACT TEXT:
{context}

Respond with a JSON object:
{{
    "detected": true/false,
    "finding": "Financial risk identified",
    "evidence": "Relevant contract terms",
    "risk_level": "low/medium/high/critical",
    "explanation": "Financial impact assessment",
    "recommendation": "Mitigation strategy",
    "metadata": {{
        "net_payment_days": integer (e.g. 30, 60, 90),
        "penalty_percentage": float (e.g. 5.0),
        "is_one_sided": boolean,
        "has_auto_renewal": boolean,
        "has_price_escalation": boolean,
        "has_rate_card": boolean,
        "undefined_drivers": integer,
        "total_drivers": integer (default 5)
    }}
}}

Focus on:
- Payment: Net days.
- Penalties: % amounts.
- Revenue: Renewal, escalation.
"""

    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        return []
