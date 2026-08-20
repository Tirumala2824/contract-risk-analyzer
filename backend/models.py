"""
Pydantic models for request/response schemas and database documents.
Defines all data structures used across the application.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """Analysis status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class RiskDomain(str, Enum):
    """Risk analysis domains."""
    LEGAL = "legal"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    SECURITY = "security"
    FRAUD = "fraud"


class AnalysisMode(str, Enum):
    """Analysis mode: Pre-signed or Post-signed."""
    PRE_SIGNED = "pre_signed"
    POST_SIGNED = "post_signed"


class RiskAction(str, Enum):
    """Recommended action based on risk and confidence."""
    AUTO_APPROVE = "auto_approve"
    SENIOR_REVIEW = "senior_review"
    MANDATORY_REVIEW = "mandatory_review"


# ============================================================================
# Risk Finding Models
# ============================================================================

class RiskFinding(BaseModel):
    """Individual risk finding from an agent."""
    parameter: str = Field(..., description="Risk parameter analyzed")
    detected: bool = Field(..., description="Whether issue was detected")
    finding: str = Field(..., description="What was detected or checked")
    evidence: Optional[str] = Field(None, description="Extracted text evidence")
    risk_level: RiskLevel = Field(..., description="Risk level for this finding")
    score: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    explanation: str = Field(..., description="Why this score was assigned")
    recommendation: Optional[str] = Field(None, description="Suggested action")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw extraction data for deterministic scoring")


class JudgeScore(BaseModel):
    """Breakdown of scores from different judges."""
    rule_score: float = Field(..., ge=0, le=100)
    template_score: float = Field(..., ge=0, le=100)
    bayes_score: float = Field(..., ge=0, le=100)
    llm_score: float = Field(..., ge=0, le=100)


class DomainRiskResult(BaseModel):
    """Risk analysis result for a single domain."""
    domain: RiskDomain = Field(..., description="Risk domain")
    findings: List[RiskFinding] = Field(default_factory=list)
    domain_score: float = Field(..., ge=0, le=100, description="Aggregate domain score")
    domain_level: RiskLevel = Field(..., description="Overall domain risk level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the score (0-1)")
    judge_scores: Optional[JudgeScore] = Field(None, description="Score breakdown by judge")
    risk_action: Optional[RiskAction] = Field(None, description="Recommended action")
    summary: str = Field(..., description="Domain analysis summary")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class OverallRiskScore(BaseModel):
    """Overall contract risk assessment."""
    overall_score: float = Field(..., ge=0, le=100)
    overall_level: RiskLevel
    status: str = Field(..., description="Overall contract status (e.g. BLOCKED)")
    domain_scores: Dict[str, float] = Field(default_factory=dict)
    executive_summary: str
    key_risks: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


# ============================================================================
# Document Models
# ============================================================================

class DocumentMetadata(BaseModel):
    """Document metadata."""
    pages: Optional[int] = None
    word_count: Optional[int] = None
    sheets: Optional[List[str]] = None  # For Excel files


class DocumentChunk(BaseModel):
    """Text chunk for RAG processing."""
    chunk_id: int
    text: str
    start_page: Optional[int] = None


class DocumentBase(BaseModel):
    """Base document model."""
    filename: str
    original_name: str
    file_type: FileType
    file_path: str


class DocumentCreate(DocumentBase):
    """Document creation model."""
    pass


class DocumentInDB(DocumentBase):
    """Document stored in database."""
    id: str = Field(..., alias="_id")
    upload_time: datetime
    status: DocumentStatus
    extracted_text: Optional[str] = None
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Optional[DocumentMetadata] = None
    error_message: Optional[str] = None
    
    class Config:
        populate_by_name = True


class DocumentResponse(BaseModel):
    """Document API response."""
    id: str
    filename: str
    original_name: str
    file_type: FileType
    upload_time: datetime
    status: DocumentStatus
    metadata: Optional[DocumentMetadata] = None


# ============================================================================
# Analysis Models
# ============================================================================

class AnalysisCreate(BaseModel):
    """Analysis creation request."""
    document_id: str
    mode: AnalysisMode = Field(default=AnalysisMode.PRE_SIGNED, description="Analysis mode")
    reference_document_id: Optional[str] = Field(None, description="Optional reference document ID")


class AnalysisInDB(BaseModel):
    """Analysis stored in database."""
    id: str = Field(..., alias="_id")
    document_id: str
    mode: AnalysisMode = Field(default=AnalysisMode.PRE_SIGNED)
    reference_document_id: Optional[str] = None
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    risk_scores: Dict[str, DomainRiskResult] = Field(default_factory=dict)
    overall_score: Optional[float] = None
    overall_level: Optional[RiskLevel] = None
    executive_summary: Optional[str] = None
    error_message: Optional[str] = None
    
    class Config:
        populate_by_name = True


class AnalysisStatusResponse(BaseModel):
    """Analysis status response."""
    id: str
    document_id: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: Optional[Dict[str, str]] = None


class AnalysisResultResponse(BaseModel):
    """Full analysis result response."""
    id: str
    document_id: str
    document_name: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    risk_scores: Dict[str, DomainRiskResult]
    overall_score: float
    overall_level: RiskLevel
    executive_summary: str


class DomainResultResponse(BaseModel):
    """Single domain result response."""
    domain: RiskDomain
    domain_score: float
    domain_level: RiskLevel
    summary: str
    findings: List[RiskFinding]


# ============================================================================
# Audit Models
# ============================================================================

class AuditLogAction(str, Enum):
    """Audit log action types."""
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_PROCESSED = "document_processed"
    ANALYSIS_STARTED = "analysis_started"
    AGENT_COMPLETED = "agent_completed"
    ANALYSIS_COMPLETED = "analysis_completed"
    ERROR_OCCURRED = "error_occurred"


class AuditLog(BaseModel):
    """Audit log entry."""
    id: str = Field(..., alias="_id")
    document_id: str
    analysis_id: Optional[str] = None
    action: AuditLogAction
    timestamp: datetime
    agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True


class AuditLogCreate(BaseModel):
    """Audit log creation request."""
    document_id: str
    analysis_id: Optional[str] = None
    action: AuditLogAction
    agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# API Response Models
# ============================================================================

class UploadResponse(BaseModel):
    """Document upload response."""
    success: bool
    message: str
    document_id: str
    analysis_id: str


class ErrorResponse(BaseModel):
    """Error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
