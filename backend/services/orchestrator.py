import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from bson import ObjectId # Used for ID compatibility if needed, though Repos handle it.

from ..models import (
    RiskDomain, RiskLevel, AnalysisStatus, DomainRiskResult,
    AuditLogAction, AnalysisMode
)
from ..core.config import RISK_DOMAIN_WEIGHTS, RISK_LEVELS
from ..interfaces.services import IOrchestrationService
from ..interfaces.analysis import IAnalysisRepository
from ..interfaces.documents import IDocumentRepository
from ..interfaces.audit import IAuditRepository

from ..agents.factory import AgentFactory
from ..agents.comparator import ReferenceComparatorAgent
from .scoring import ScoringEngine

logger = logging.getLogger(__name__)

class OrchestrationService(IOrchestrationService):
    """Service for orchestrating multi-agent analysis."""
    
    def __init__(
        self,
        analysis_repository: IAnalysisRepository,
        document_repository: IDocumentRepository,
        audit_repository: IAuditRepository
    ):
        self.analysis_repository = analysis_repository
        self.document_repository = document_repository
        self.audit_repository = audit_repository
        self.scoring_engine = ScoringEngine()

    async def create_analysis(
        self, 
        document_id: str, 
        mode: AnalysisMode = AnalysisMode.PRE_SIGNED,
        reference_document_id: Optional[str] = None
    ) -> str:
        analysis_data = {
            "document_id": document_id,
            "mode": mode.value,
            "reference_document_id": reference_document_id,
            "status": AnalysisStatus.PENDING.value,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "risk_scores": {},
            "overall_score": None
        }
        
        analysis_id = await self.analysis_repository.add(analysis_data)
        
        await self.audit_repository.add({
            "document_id": document_id,
            "analysis_id": analysis_id,
            "action": AuditLogAction.ANALYSIS_STARTED.value,
            "timestamp": datetime.utcnow(),
            "details": {"status": "Analysis created"}
        })
        
        return analysis_id

    async def run_analysis(self, analysis_id: str) -> bool:
        try:
            analysis = await self.analysis_repository.get(analysis_id)
            if not analysis:
                logger.error(f"Analysis not found: {analysis_id}")
                return False
            
            document_id = analysis["document_id"]
            doc = await self.document_repository.get(document_id)
            
            if not doc or not doc.get("extracted_text"):
                logger.error(f"Document not ready: {document_id}")
                await self.analysis_repository.update_status(analysis_id, AnalysisStatus.FAILED, "Document not processed")
                return False
            
            await self.analysis_repository.update_status(analysis_id, AnalysisStatus.IN_PROGRESS)
            
            text = doc["extracted_text"]
            chunks = doc.get("chunks", [])
            
            # Run Agents
            agents = AgentFactory.get_all_agents()
            tasks = [self._run_agent(agent, text, chunks, document_id, analysis_id) for agent in agents]
            
            # Reference Comparison
            ref_id = analysis.get("reference_document_id")
            if ref_id:
                tasks.append(self._run_comparison(analysis_id, document_id, text, chunks, ref_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            domain_results: Dict[str, DomainRiskResult] = {}
            
            # Re-score using Scoring Engine
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Agent error: {result}")
                    continue
                if result:
                    # The agent returns a preliminary result. We extract findings and run through Scoring Engine.
                    # This ensures consistency and applies the multi-model consensus.
                    advanced_result = await self.scoring_engine.analyze_domain(result.domain, result.findings)
                    domain_results[result.domain.value] = advanced_result

            # Overall Score using Engine
            overall_result = self.scoring_engine.calculate_overall_score(domain_results)
            
            # Prepare update data compatible with DB schema
            # We need to serialize the complex objects
            serialized_scores = {k: v.model_dump() for k, v in domain_results.items()}
            
            update_data = {
                "risk_scores": serialized_scores,
                "overall_score": overall_result.overall_score,
                "overall_level": overall_result.overall_level.value,
                "executive_summary": overall_result.executive_summary,
                "status": AnalysisStatus.COMPLETED
            }
            
            await self.analysis_repository.update_results(analysis_id, update_data)
            
            await self.audit_repository.add({
                "document_id": document_id,
                "analysis_id": analysis_id,
                "action": AuditLogAction.ANALYSIS_COMPLETED.value,
                "timestamp": datetime.utcnow(),
                "details": {
                    "overall_score": overall_result.overall_score,
                    "overall_level": overall_result.overall_level.value
                }
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            await self.analysis_repository.update_status(analysis_id, AnalysisStatus.FAILED, str(e))
            return False

    async def _run_agent(self, agent, text, chunks, document_id, analysis_id):
        # ... logic ...
        try:
            result = await agent.analyze(text, chunks)
            # Log completion...
            return result
        except Exception as e:
            logger.error(f"Agent {agent.domain.value} failed: {e}")
            return None

    async def _run_comparison(self, analysis_id, document_id, target_text, target_chunks, ref_id):
        # ... logic ...
        ref_doc = await self.document_repository.get(ref_id)
        if not ref_doc: return None
        
        comparator = ReferenceComparatorAgent()
        findings = await comparator.compare(target_text, ref_doc["extracted_text"], target_chunks, ref_doc.get("chunks", []))
        
        score = 50.0
        if findings:
             score = max(0, 100 - (len(findings) * 10))
             
        return DomainRiskResult(
            domain=RiskDomain.LEGAL, # Use Legal for now as proxy
            findings=findings,
            domain_score=score,
            domain_level=RiskLevel.MEDIUM,
            confidence_score=0.8,
            summary=f"Comparison: {len(findings)} deviations.",
            analyzed_at=datetime.utcnow()
        )

    def _generate_executive_summary(self, domain_results, overall_score, overall_level):
        # ... existing logic ...
        return f"Assessment: {overall_level.value} (Score: {overall_score})"

    async def get_analysis_status(self, analysis_id: str) -> Optional[dict]:
        analysis = await self.analysis_repository.get(analysis_id)
        if not analysis: return None
        return {
            "id": str(analysis.get("_id") or analysis.get("id")),
            "document_id": analysis["document_id"],
            "status": analysis["status"],
            "created_at": analysis["created_at"]
        }

    async def get_analysis_results(self, analysis_id: str) -> Optional[dict]:
        analysis = await self.analysis_repository.get(analysis_id)
        if not analysis: return None
        doc = await self.document_repository.get(analysis["document_id"])
        
        return {
            "id": str(analysis.get("_id") or analysis.get("id")),
            "document_id": analysis["document_id"],
            "document_name": doc["original_name"] if doc else "Unknown",
            "status": analysis["status"],
            "created_at": analysis["created_at"],
            "completed_at": analysis.get("completed_at"),
            "risk_scores": analysis.get("risk_scores") or {},
            "overall_score": analysis.get("overall_score") or 0.0,
            "overall_level": analysis.get("overall_level") or RiskLevel.LOW,
            "executive_summary": analysis.get("executive_summary") or "Analysis in progress..."
        }

    async def list_analyses(self, limit: int = 50, skip: int = 0) -> list:
        """List all analyses for history page."""
        analyses = await self.analysis_repository.list(limit=limit, skip=skip)
        results = []
        for analysis in analyses:
            doc = await self.document_repository.get(analysis["document_id"])
            results.append({
                "id": str(analysis.get("_id") or analysis.get("id")),
                "document_id": analysis["document_id"],
                "document_name": doc["original_name"] if doc else "Unknown",
                "status": analysis["status"],
                "created_at": analysis["created_at"],
                "overall_score": analysis.get("overall_score"),
                "overall_level": analysis.get("overall_level")
            })
        return results
