import logging
import datetime
from typing import List, Dict, Optional, Tuple

from llama_index.core import Document, VectorStoreIndex
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

from ..models import RiskDomain, RiskLevel, RiskFinding, DomainRiskResult
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class ReferenceComparatorAgent:
    """Agent for comparing a document against a reference template."""
    
    def __init__(self):
        self.settings = get_settings()
        self._setup_llm()
        
    def _setup_llm(self):
        # ... logic similar to BaseRiskAgent ...
        if self.settings.azure_openai_api_key:
             self.llm = AzureOpenAI(
                model=self.settings.azure_openai_model,
                deployment_name=self.settings.azure_openai_model,
                api_key=self.settings.azure_openai_api_key,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version,
                temperature=0.1
            )
        elif self.settings.openai_api_key:
            self.llm = OpenAI(model="gpt-4o-mini", api_key=self.settings.openai_api_key)
        else:
            self.llm = None

    async def compare(
        self, 
        target_text: str, 
        reference_text: str,
        target_chunks: List[Dict],
        ref_chunks: List[Dict]
    ) -> List[RiskFinding]:
        """Compare target document against reference."""
        logger.info("Starting reference comparison...")
        findings = []
        
        if not reference_text:
            logger.warning("No reference text provided for comparison")
            return []

        if not self.llm:
            return []

        # 1. Index Reference Document
        ref_documents = [Document(text=c["text"]) for c in ref_chunks]
        if not ref_documents:
            ref_documents = [Document(text=reference_text)]
            
        ref_index = VectorStoreIndex.from_documents(ref_documents)
        ref_retriever = ref_index.as_retriever(similarity_top_k=5)

        # 2. Key Clauses to Compare
        key_clauses = [
            "Limitation of Liability",
            "Indemnification",
            "Termination",
            "Governing Law",
            "Payment Terms",
            "Confidentiality",
            "Warranties",
            "Data Protection"
        ]

        # 3. Index Target
        target_documents = [Document(text=c["text"]) for c in target_chunks]
        if not target_documents:
            target_documents = [Document(text=target_text)]
        
        target_index = VectorStoreIndex.from_documents(target_documents)
        target_retriever = target_index.as_retriever(similarity_top_k=3)

        for clause_name in key_clauses:
            try:
                # Find in Reference
                ref_nodes = ref_retriever.retrieve(clause_name)
                ref_context = "\n".join([n.get_content() for n in ref_nodes])
                
                # Find in Target
                target_nodes = target_retriever.retrieve(clause_name)
                target_context = "\n".join([n.get_content() for n in target_nodes])

                # Compare
                finding = await self._analyze_deviation(clause_name, ref_context, target_context)
                if finding:
                    findings.append(finding)
                    
            except Exception as e:
                logger.error(f"Error comparing clause {clause_name}: {e}")

        return findings

    async def _analyze_deviation(self, clause_name: str, ref_text: str, target_text: str) -> Optional[RiskFinding]:
        prompt = f"""Compare the '{clause_name}' clause.
REFERENCE:
{ref_text[:1500]}

TARGET:
{target_text[:1500]}

Determine if the Target matches the Reference. If missing, weaker, or significantly different, report it.
Respond with JSON:
{{
    "detected": true/false,
    "deviation_type": "missing"|"weaker"|"different"|"matched",
    "finding": "Description",
    "risk_level": "low"|"medium"|"high"|"critical",
    "score": 0-100,
    "explanation": "Rationale"
}}
"""
        try:
            response = await self.llm.acomplete(prompt)
            return self._parse_comparison_response(str(response), clause_name)
        except Exception as e:
            logger.error(f"LLM comparison failed for {clause_name}: {e}")
            return None

    def _parse_comparison_response(self, response: str, clause_name: str) -> Optional[RiskFinding]:
        import json
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                if not data.get("detected") or data.get("deviation_type") == "matched":
                    return None

                return RiskFinding(
                    parameter=f"Deviation: {clause_name}",
                    detected=True,
                    finding=data.get("finding", f"Deviation in {clause_name}"),
                    evidence=None,
                    risk_level=RiskLevel(data.get("risk_level", "medium").lower()),
                    score=min(100, max(0, int(data.get("score", 50)))),
                    explanation=data.get("explanation", ""),
                    recommendation="Revert to reference standard or justify deviation."
                )
        except Exception:
            return None
        return None
