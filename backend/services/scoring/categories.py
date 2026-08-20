from typing import List
from .base import RiskCategoryScorer
from ...models import RiskFinding

class LegalScorer(RiskCategoryScorer):
    """Category A: Legal & Contractual Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            # Fallback if metadata is missing (covers Error, Not Detected, or Parse Fail cases)
            if not meta:
                score = f.score
                weight = 0.20 # Default weight
            else:
                if f.parameter == "Ambiguous Clauses":
                    k = meta.get("ambiguous_count", 0)
                    score = min(100, 20 * k)
                    weight = 0.20
                elif f.parameter == "Missing Obligations":
                    m = meta.get("missing_count", 0)
                    e = meta.get("expected_count", 1)
                    score = min(100, 100 * (m / e))
                    weight = 0.25
                elif f.parameter == "Liability Exposure":
                    cap_type = meta.get("cap_type", "equal")
                    mapping = {"unlimited": 100, "no_cap": 90, "worse": 70, "equal": 40, "better": 20}
                    score = mapping.get(cap_type, 40)
                    weight = 0.25
                elif f.parameter == "Termination Risk":
                    asymmetry = 1 if meta.get("asymmetry", False) else 0
                    no_cure = 1 if meta.get("no_cure", False) else 0
                    no_notice = 1 if meta.get("no_notice", False) else 0
                    score = min(100, 50 * asymmetry + 30 * no_cure + 20 * no_notice)
                    weight = 0.20
                elif f.parameter == "Jurisdiction Mismatch":
                    mismatch_type = meta.get("mismatch_type", "aligned")
                    mapping = {"different_country": 80, "different_venue": 40, "aligned": 10}
                    score = mapping.get(mismatch_type, 10)
                    weight = 0.10
            
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
        
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0

class ComplianceScorer(RiskCategoryScorer):
    """Category B: Compliance & Regulatory Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            if not meta:
                score = f.score
                weight = 0.25
            else:
                if f.parameter == "Policy Violations":
                    missing = meta.get("missing_mandatory", 0)
                    total = meta.get("total_mandatory", 1)
                    score = min(100, 100 * (missing / total))
                    weight = 0.30
                elif f.parameter == "Regulatory Gaps":
                    missing = meta.get("missing_regs", 0)
                    applicable = meta.get("applicable_regs", 1)
                    score = min(100, 100 * (missing / applicable))
                    weight = 0.30
                elif f.parameter == "Audit Readiness":
                    score = 0
                    if not meta.get("has_approval_workflow", True): score += 40
                    if not meta.get("has_audit_trail", True): score += 40
                    if not meta.get("has_responsible_party", True): score += 20
                    score = min(100, score)
                    weight = 0.20
                elif f.parameter == "Non-Standard Language":
                    sim = meta.get("similarity_score", 1.0) # 0.0 to 1.0
                    score = 100 * (1 - sim)
                    weight = 0.20
                
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
                
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0

class FinancialScorer(RiskCategoryScorer):
    """Category C: Financial & Commercial Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            if not meta:
                score = f.score
                weight = 0.25
            else:
                if f.parameter == "Payment Terms":
                    days = meta.get("net_payment_days", 30)
                    score = min(100, (days / 90) * 100)
                    weight = 0.30
                elif f.parameter == "Penalty Clauses":
                    penalty_pct = meta.get("penalty_percentage", 0)
                    asymmetry = 1.5 if meta.get("is_one_sided", False) else 1.0
                    score = min(100, penalty_pct * asymmetry)
                    weight = 0.25
                elif f.parameter == "Revenue Leakage":
                    score = 0
                    if not meta.get("has_auto_renewal", True): score += 30
                    if not meta.get("has_price_escalation", True): score += 30
                    if not meta.get("has_rate_card", True): score += 40
                    score = min(100, score)
                    weight = 0.25
                elif f.parameter == "Cost Ambiguity":
                    undefined = meta.get("undefined_drivers", 0)
                    total = meta.get("total_drivers", 1)
                    score = min(100, 100 * (undefined / total))
                    weight = 0.20
            
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
        
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0

class OperationalScorer(RiskCategoryScorer):
    """Category D: Operational & Process Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            if not meta:
                score = f.score
                weight = 0.25
            else:
                if f.parameter == "Role Ambiguity":
                    unassigned = meta.get("unassigned_roles", 0)
                    total = meta.get("total_roles", 1)
                    score = min(100, 100 * (unassigned / total))
                    weight = 0.25
                elif f.parameter == "Missing Controls":
                    missing = meta.get("missing_controls", 0)
                    required = meta.get("required_controls", 1)
                    score = min(100, 100 * (missing / required))
                    weight = 0.25
                elif f.parameter == "SLA Risk":
                    score = 0
                    if not meta.get("has_delivery_timeline", True): score += 30
                    if not meta.get("has_response_sla", True): score += 30
                    if not meta.get("has_uptime_guarantee", True): score += 40
                    score = min(100, score)
                    weight = 0.30
                elif f.parameter == "Dependency Risk":
                    unallocated = meta.get("unallocated_risks", 0)
                    total = meta.get("total_risks", 1)
                    score = min(100, 100 * (unallocated / total))
                    weight = 0.20
            
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
        
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0

class SecurityScorer(RiskCategoryScorer):
    """Category E: Security & Data Privacy Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            if not meta:
                score = f.score
                weight = 0.25
            else:
                if f.parameter == "PII Exposure":
                    has_pii = meta.get("has_pii", False)
                    protection = meta.get("protection_level", "none") # none, weak, strong
                    if not has_pii:
                        score = 0
                    elif protection == "none":
                        score = 100
                    elif protection == "weak":
                        score = 50
                    else: 
                        score = 10
                    weight = 0.30
                elif f.parameter == "Data Retention Gaps":
                    missing = meta.get("missing_retention_elements", 0)
                    required = meta.get("required_retention_elements", 1)
                    score = min(100, 100 * (missing / required))
                    weight = 0.20
                elif f.parameter == "Security Obligations":
                    score = 0
                    if not meta.get("has_encryption", True): score += 30
                    if not meta.get("has_access_control", True): score += 30
                    if not meta.get("has_certification", True): score += 40
                    score = min(100, score)
                    weight = 0.30
                elif f.parameter == "Breach Responsibility":
                    score = 0
                    if not meta.get("has_notification_timeline", True): score += 50
                    if not meta.get("has_accountability", True): score += 50
                    score = min(100, score)
                    weight = 0.20
            
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
        
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0

class FraudScorer(RiskCategoryScorer):
    """Category F: Fraud & Manipulation Risk"""
    
    def calculate_base_score(self, findings: List[RiskFinding]) -> float:
        scores = []
        weights = []
        
        for f in findings:
            meta = f.metadata
            score = 0.0
            weight = 0.0
            
            if not meta:
                score = f.score
                weight = 0.25
            else:
                if f.parameter == "Document Tampering":
                    score = min(100, 100 * meta.get("tampering_anomaly_score", 0.0))
                    weight = 0.30
                elif f.parameter == "Unusual Language":
                    score = min(100, 100 * meta.get("language_anomaly_index", 0.0))
                    weight = 0.20
                elif f.parameter == "Inconsistent Values":
                    conflicting = meta.get("conflicting_fields", 0)
                    critical = meta.get("critical_fields", 1)
                    score = min(100, 100 * (conflicting / critical))
                    weight = 0.30
                elif f.parameter == "Duplicate Content":
                    score = min(100, 100 * meta.get("duplication_severity", 0.0))
                    weight = 0.20
                
            if weight > 0:
                scores.append(score * weight)
                weights.append(weight)
        
        total_weight = sum(weights)
        return sum(scores) / total_weight if total_weight > 0 else 0.0
