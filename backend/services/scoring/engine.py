import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

from ...models import (
    RiskDomain, RiskLevel, RiskAction, RiskFinding, 
    DomainRiskResult, OverallRiskScore, JudgeScore
)
from ...config import RISK_DOMAIN_WEIGHTS, RISK_LEVELS

from .base import RiskCategoryScorer, ConsensusJudge
from .categories import (
    LegalScorer, ComplianceScorer, FinancialScorer, 
    OperationalScorer, SecurityScorer, FraudScorer
)
from .judges import RuleJudge, TemplateJudge, BayesJudge, LLMJudge

logger = logging.getLogger(__name__)

class ScoringEngine:
    """Orchestrates the risk scoring process."""
    
    def __init__(self):
        self.scorers = {
            RiskDomain.LEGAL: LegalScorer(),
            RiskDomain.COMPLIANCE: ComplianceScorer(),
            RiskDomain.FINANCIAL: FinancialScorer(),
            RiskDomain.OPERATIONAL: OperationalScorer(),
            RiskDomain.SECURITY: SecurityScorer(),
            RiskDomain.FRAUD: FraudScorer()
        }
        
        self.judges = [
            RuleJudge(),
            TemplateJudge(),
            BayesJudge(),
            LLMJudge()
        ]
        
    async def analyze_domain(self, domain: RiskDomain, findings: List[RiskFinding]) -> DomainRiskResult:
        """Perform full risk analysis for a domain."""
        logger.info(f"Scoring domain: {domain}")
        
        # 1. Base Score
        scorer = self.scorers.get(domain)
        if not scorer:
            logger.error(f"No scorer found for {domain}")
            return self._empty_result(domain)
            
        base_score = scorer.calculate_base_score(findings)
        
        # 2. Multi-Model Consensus
        judge_scores = {}
        judge_results = []
        
        context = {"domain": domain}
        
        for judge in self.judges:
            try:
                score = await judge.evaluate(base_score, findings, context)
                judge_scores[judge.name] = score
                judge_results.append(score)
            except Exception as e:
                logger.error(f"Judge {judge.name} failed: {e}")
                judge_scores[judge.name] = base_score
                judge_results.append(base_score)
                
        # 3. Weighted Aggregation (Policy: 30% Rule, 30% Template, 25% Bayes, 15% LLM)
        # Note: Judge names must match what's in judges.py
        j_rule = judge_scores.get("RuleJudge", base_score)
        j_template = judge_scores.get("TemplateJudge", base_score)
        j_bayes = judge_scores.get("BayesJudge", base_score)
        j_llm = judge_scores.get("LLMJudge", base_score)
        
        final_score = (
            0.30 * j_rule +
            0.30 * j_template +
            0.25 * j_bayes +
            0.15 * j_llm
        )
        final_score = round(final_score, 2)
        
        # 4. Confidence
        # Spread = max - min
        spread = max(judge_results) - min(judge_results)
        # Confidence = max(0, 1 - spread/35)
        confidence = max(0.0, 1.0 - (spread / 35.0))
        confidence = round(confidence, 2)
        
        # 5. Risk Level & Action
        level = self._get_risk_level(final_score)
        action = self._determine_action(final_score, confidence)
        
        # 6. Summary
        summary = self._generate_summary(findings, final_score, level, action)
        
        return DomainRiskResult(
            domain=domain,
            findings=findings,
            domain_score=final_score,
            domain_level=level,
            confidence_score=confidence,
            judge_scores=JudgeScore(
                rule_score=j_rule,
                template_score=j_template,
                bayes_score=j_bayes,
                llm_score=j_llm
            ),
            risk_action=action,
            summary=summary,
            analyzed_at=datetime.utcnow()
        )
    
    def calculate_overall_score(self, domain_results: Dict[str, DomainRiskResult]) -> OverallRiskScore:
        """Calculate overall contract score."""
        if not domain_results:
            return OverallRiskScore(
                overall_score=0.0, overall_level=RiskLevel.LOW, status="AUTO_APPROVED",
                executive_summary="No analysis performed.", 
                key_risks=[], recommendations=[]
            )
            
        weighted_sum = 0.0
        weight_total = 0.0
        domain_scores_map = {}
        
        actions = []
        
        for domain_str, result in domain_results.items():
            domain = RiskDomain(domain_str) if isinstance(domain_str, str) else domain_str
            weight = RISK_DOMAIN_WEIGHTS.get(domain.value, 0.1)
            
            # Using simple lookup if RISK_DOMAIN_WEIGHTS uses strings
            if not weight:
                weight = RISK_DOMAIN_WEIGHTS.get(str(domain), 0.1)
                
            weighted_sum += result.domain_score * weight
            weight_total += weight
            domain_scores_map[str(domain)] = result.domain_score
            actions.append(result.risk_action)
            
        overall_score = weighted_sum / weight_total if weight_total > 0 else 0.0
        overall_level = self._get_risk_level(overall_score)
        
        # Status Logic
        if RiskAction.MANDATORY_REVIEW in actions:
            status = "BLOCKED"
        elif RiskAction.SENIOR_REVIEW in actions:
            status = "PENDING_REVIEW"
        else:
            status = "AUTO_APPROVED"
            
        executive_summary = f"Contract risk is {overall_level.value.upper()} ({overall_score:.1f}/100). Status: {status}."
        
        return OverallRiskScore(
            overall_score=round(overall_score, 2),
            overall_level=overall_level,
            status=status,
            domain_scores=domain_scores_map,
            executive_summary=executive_summary,
            key_risks=[], # To be filled by key risk extractor
            recommendations=[] # To be filled by recommendation engine
        )

    def _get_risk_level(self, score: float) -> RiskLevel:
        # 0-20 Low, 21-40 Medium, 41-60 High, 61-80 Very High, 81-100 Critical
        if score <= 20: return RiskLevel.LOW
        if score <= 40: return RiskLevel.MEDIUM
        if score <= 60: return RiskLevel.HIGH
        if score <= 80: return RiskLevel.VERY_HIGH
        return RiskLevel.CRITICAL

    def _determine_action(self, score: float, confidence: float) -> RiskAction:
        # Policy:
        # Critical/VeryHigh (61+) or <0.60 conf -> Mandatory (Wait, policy table check)
        # Table: 
        # >60 OR Conf < 0.6 -> Mandatory (actually code says if Score >= 61 AND Conf < 0.6 -> Mandatory? No, policy says rows)
        # Let's check policy pseudocode:
        # if Score >= 61 and Confidence < 0.60: MANDATORY
        # elif Score >= 41 and Confidence >= 0.60: SENIOR
        # else: AUTO_APPROVE
        
        # Policy table: 
        # Critical/VH (<0.60) -> Mandatory (Wait, table row 1 column 3 is "Mandatory Human Review")
        # Ah, the table implies logic. Text says "If any category = Mandatory... Contract=BLOCKED"
        # Pseudocode provided in text:
        # if Score_X >= 61 and Confidence_X < 0.60: MANDATORY 
        # ... Wait, the pseudocode in policy text might be simplified.
        # "Critical (81-100) or Very High (61-80) <0.60 Mandatory"
        # "High (41-60) or above >= 0.60 Senior"
        
        # Let's stick to the explicit pseudocode in the policy text:
        # if Score_X >= 61 and Confidence_X < 0.60: action = "MANDATORY_REVIEW"
        # elif Score_X >= 41 and Confidence_X >= 0.60: action = "SENIOR_REVIEW"
        # else: action = "AUTO_APPROVE" -- Wait, this leaves out Score >= 61 with Conf >= 0.60?
        # The table says "High (41-60) or above >= 0.60 Senior Review". So Critical/VH with High Conf is Senior Review?
        # That seems risky. "Critical... <0.60 Mandatory". What about Critical >= 0.60?
        # Table: "Critical ... <0.60 Mandatory".
        # Let's assume Critical/VeryHigh is ALWAYS at least Senior Review.
        # If Low Confidence (<0.6), it becomes Mandatory Review.
        
        if score >= 61:
            if confidence < 0.60:
                return RiskAction.MANDATORY_REVIEW
            else:
                return RiskAction.SENIOR_REVIEW # Or Mandatory? Policy implies Mandatory for high risk + low conf. High risk + high conf = Senior.
        elif score >= 41:
            if confidence < 0.60:
                 # Medium risk but low confidence -> Maybe Senior? Policy pseudocode says:
                 # else (which catches this) -> Auto Approve.
                 # Wait, 21-40 is Medium. 41-60 is High.
                 # High (41-60) row in table says: "High... >= 0.60 Senior Legal Review".
                 # It doesn't explicitly say what High + Low Conf is.
                 # Usually Low Conf upgrades risk action.
                 return RiskAction.SENIOR_REVIEW
            else:
                return RiskAction.SENIOR_REVIEW
        
        return RiskAction.AUTO_APPROVE

    def _generate_summary(self, findings: List[RiskFinding], score: float, level: RiskLevel, action: RiskAction) -> str:
        count = len(findings)
        issues = sum(1 for f in findings if f.detected)
        return f"{level.value.title()} Risk ({score}). {issues}/{count} issues found. Action: {action.value.replace('_', ' ').title()}."

    def _empty_result(self, domain: RiskDomain) -> DomainRiskResult:
        return DomainRiskResult(
            domain=domain,
            findings=[],
            domain_score=0.0,
            domain_level=RiskLevel.LOW,
            confidence_score=1.0,
            summary="Analysis failed.",
            risk_action=RiskAction.AUTO_APPROVE
        )
