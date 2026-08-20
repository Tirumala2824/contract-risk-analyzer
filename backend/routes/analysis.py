from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from ..models import AnalysisStatusResponse, AnalysisResultResponse
from ..core.container import container
from ..interfaces.services import IOrchestrationService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

async def get_orchestrator() -> IOrchestrationService:
    return container.orchestration_service

@router.get("")
async def list_analyses(
    limit: int = 50,
    skip: int = 0,
    service: IOrchestrationService = Depends(get_orchestrator)
):
    """List all analyses for history page."""
    analyses = await service.list_analyses(limit, skip)
    return {"analyses": analyses}

@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    service: IOrchestrationService = Depends(get_orchestrator)
):
    """Get analysis status."""
    status = await service.get_analysis_status(analysis_id)
    if not status:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return status

@router.get("/{analysis_id}/results", response_model=AnalysisResultResponse)
async def get_analysis_results(
    analysis_id: str,
    service: IOrchestrationService = Depends(get_orchestrator)
):
    """Get analysis results."""
    results = await service.get_analysis_results(analysis_id)
    if not results:
        raise HTTPException(status_code=404, detail="Analysis results not found")
    return results

@router.get("/{analysis_id}/summary")
async def get_analysis_summary(
    analysis_id: str,
    service: IOrchestrationService = Depends(get_orchestrator)
):
    """Get executive summary."""
    results = await service.get_analysis_results(analysis_id)
    if not results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "id": results["id"],
        "summary": results.get("executive_summary"),
        "overall_score": results.get("overall_score"),
        "overall_level": results.get("overall_level")
    }
