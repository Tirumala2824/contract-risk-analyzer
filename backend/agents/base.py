import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

from llama_index.core import Document, VectorStoreIndex, Settings as LlamaSettings
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from ..models import RiskDomain, RiskLevel, RiskFinding, DomainRiskResult
from ..core.config import get_settings, RISK_LEVELS

logger = logging.getLogger(__name__)

def get_risk_level(score: int) -> RiskLevel:
    """Convert numeric score to risk level."""
    for level, (low, high) in RISK_LEVELS.items():
        if low <= score <= high:
            return RiskLevel(level)
    return RiskLevel.HIGH

class IRiskAgent(ABC):
    """Interface for risk/analysis agents."""
    
    @abstractmethod
    async def analyze(self, text: str, chunks: List[Dict]) -> DomainRiskResult:
        pass

class BaseRiskAgent(IRiskAgent):
    """Base class for all risk analysis agents."""
    
    def __init__(self, domain: RiskDomain):
        self.domain = domain
        self.settings = get_settings()
        self._setup_llm()
    
    def _setup_llm(self):
        """Initialize LlamaIndex with Azure OpenAI or OpenAI."""
        if self.settings.azure_openai_api_key and self.settings.azure_openai_endpoint:
             self.llm = AzureOpenAI(
                model=self.settings.azure_openai_model,
                deployment_name=self.settings.azure_openai_model,
                api_key=self.settings.azure_openai_api_key,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version,
                temperature=0.1
            )
             self.embed_model = AzureOpenAIEmbedding(
                model=self.settings.azure_embedding_model,
                deployment_name=self.settings.azure_embedding_model,
                api_key=self.settings.azure_openai_api_key,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version
            )
             LlamaSettings.llm = self.llm
             LlamaSettings.embed_model = self.embed_model
        elif self.settings.openai_api_key:
            self.llm = OpenAI(
                model="gpt-4o-mini",
                api_key=self.settings.openai_api_key,
                temperature=0.1
            )
            self.embed_model = OpenAIEmbedding(
                api_key=self.settings.openai_api_key
            )
            LlamaSettings.llm = self.llm
            LlamaSettings.embed_model = self.embed_model
        else:
            logger.warning("No OpenAI or Azure OpenAI API key configured")
            self.llm = None
            self.embed_model = None
    
    @property
    @abstractmethod
    def parameters(self) -> List[Dict[str, str]]:
        """Risk parameters this agent analyzes."""
        pass
    
    @abstractmethod
    def get_analysis_prompt(self, parameter: str, context: str) -> str:
        """Generate analysis prompt for a specific parameter."""
        pass
    
    async def analyze(self, text: str, chunks: List[Dict]) -> DomainRiskResult:
        """Analyze document for this risk domain."""
        logger.info(f"Starting {self.domain.value} risk analysis...")
        
        findings = []
        total_score = 0
        
        # Create index from document chunks
        documents = [Document(text=chunk["text"]) for chunk in chunks]
        
        if not documents:
            documents = [Document(text=text)]
        
        try:
            index = VectorStoreIndex.from_documents(
                documents,
                show_progress=False
            )
            query_engine = index.as_query_engine(similarity_top_k=3)
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            query_engine = None
        
        for param_info in self.parameters:
            try:
                finding = await self._analyze_parameter(
                    param_info, 
                    text, 
                    query_engine
                )
                findings.append(finding)
                total_score += finding.score
            except Exception as e:
                logger.error(f"Error analyzing {param_info['name']}: {e}")
                findings.append(RiskFinding(
                    parameter=param_info["name"],
                    detected=False,
                    finding=f"Analysis error: {str(e)}",
                    evidence=None,
                    risk_level=RiskLevel.MEDIUM,
                    score=50,
                    explanation="Unable to analyze this parameter due to an error.",
                    recommendation="Manual review recommended."
                ))
                total_score += 50
        
        domain_score = total_score / len(self.parameters) if self.parameters else 0
        domain_level = get_risk_level(int(domain_score))
        summary = self._generate_summary(findings, domain_score)
        
        return DomainRiskResult(
            domain=self.domain,
            findings=findings,
            domain_score=round(domain_score, 2),
            domain_level=domain_level,
            confidence_score=0.9, # Default confidence
            summary=summary,
            analyzed_at=datetime.utcnow()
        )
    
    async def _analyze_parameter(self, param_info: Dict[str, str], full_text: str, query_engine) -> RiskFinding:
        param_name = param_info["name"]
        param_desc = param_info["description"]
        
        if query_engine:
            try:
                context_query = f"Find sections related to: {param_desc}"
                response = query_engine.query(context_query)
                context = str(response)
            except:
                context = full_text[:3000]
        else:
            context = full_text[:3000]
        
        prompt = self.get_analysis_prompt(param_name, context)
        
        if self.llm:
            try:
                response = self.llm.complete(prompt)
                result = self._parse_llm_response(str(response), param_name)
            except Exception as e:
                logger.error(f"LLM query failed: {e}")
                result = self._fallback_analysis(param_name, param_desc, full_text)
        else:
            result = self._fallback_analysis(param_name, param_desc, full_text)
        
        return result
    
    def _parse_llm_response(self, response: str, param_name: str) -> RiskFinding:
        try:
            # Clean response of markdown
            response = response.replace("```json", "").replace("```", "").strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return RiskFinding(
                    parameter=param_name,
                    detected=data.get("detected", False),
                    finding=data.get("finding", "No specific finding"),
                    evidence=data.get("evidence"),
                    risk_level=RiskLevel(data.get("risk_level", "medium").lower()),
                    score=min(100, max(0, int(data.get("score", 50)))),
                    explanation=data.get("explanation", ""),
                    recommendation=data.get("recommendation"),
                    metadata=data.get("metadata", {})
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        
        detected = any(word in response.lower() for word in ["found", "detected", "identified", "yes"])
        score = 70 if detected else 20
        
        return RiskFinding(
            parameter=param_name,
            detected=detected,
            finding=response[:500],
            evidence=None,
            risk_level=get_risk_level(score),
            score=score,
            explanation=response[:300],
            recommendation="Review this finding manually."
        )
    
    def _fallback_analysis(self, param_name: str, param_desc: str, text: str) -> RiskFinding:
        text_lower = text.lower()
        keywords = self._get_keywords_for_parameter(param_name)
        found_keywords = [kw for kw in keywords if kw.lower() in text_lower]
        
        if found_keywords:
            detected = True
            score = 60
            finding = f"Keywords detected: {', '.join(found_keywords[:5])}"
        else:
            detected = False
            score = 30
            finding = f"No specific indicators found for {param_name}"
        
        return RiskFinding(
            parameter=param_name,
            detected=detected,
            finding=finding,
            evidence=None,
            risk_level=get_risk_level(score),
            score=score,
            explanation=f"Analysis based on keyword detection for '{param_desc}'",
            recommendation="Detailed manual review recommended."
        )
    
    def _get_keywords_for_parameter(self, param_name: str) -> List[str]:
        return []
    
    def _generate_summary(self, findings: List[RiskFinding], score: float) -> str:
        high_risk = [f for f in findings if f.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        detected = [f for f in findings if f.detected]
        
        summary_parts = [f"Analyzed {len(findings)} risk parameters."]
        if high_risk:
            summary_parts.append(f"{len(high_risk)} high-risk issues identified.")
        
        if detected:
            params = ", ".join([f.parameter for f in detected[:3]])
            summary_parts.append(f"Key concerns: {params}.")
        else:
            summary_parts.append("No major concerns detected.")
        
        return " ".join(summary_parts)
