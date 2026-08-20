import math
import logging
from typing import List, Dict, Any
from .base import ConsensusJudge
from ...models import RiskFinding
from ...config import get_settings
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.openai import OpenAI

logger = logging.getLogger(__name__)

class RuleJudge(ConsensusJudge):
    """Judge 1: Rule-Based Adjuster"""
    
    def __init__(self):
        super().__init__("RuleJudge")
    
    async def evaluate(self, base_score: float, findings: List[RiskFinding], context: Dict[str, Any]) -> float:
        score = base_score
        
        # Apply deterministic rules based on finding metadata/flags
        # Example from policy:
        # PII present & no encryption -> +20
        # Liability cap > 10M -> -10
        # Notice > 90 days -> -15
        
        for f in findings:
            meta = f.metadata
            
            # Security rules
            if f.parameter == "PII Exposure" and meta.get("has_pii") and meta.get("protection_level") == "none":
                score += 20
                
            # Legal rules
            if f.parameter == "Liability Exposure" and meta.get("cap_amount", 0) > 10_000_000:
                score -= 10
            
            if f.parameter == "Termination Risk" and meta.get("notice_days", 30) >= 90:
                score -= 15
                
            # Compliance rules
            if f.parameter == "Regulatory Gaps" and "GDPR" in meta.get("missing_reg_names", []) and not meta.get("mentioned_gdpr", False):
                score += 25
        
        return min(100, max(0, score))

class TemplateJudge(ConsensusJudge):
    """Judge 2: Template Diff Model (Cloud Embeddings)"""
    
    def __init__(self):
        super().__init__("TemplateJudge")
        self.settings = get_settings()
        self.embed_model = self._setup_embedding()
    
    def _setup_embedding(self):
        try:
            if self.settings.azure_openai_api_key and self.settings.azure_openai_endpoint:
                return AzureOpenAIEmbedding(
                    model=self.settings.azure_embedding_model,
                    deployment_name=self.settings.azure_embedding_model,
                    api_key=self.settings.azure_openai_api_key,
                    azure_endpoint=self.settings.azure_openai_endpoint,
                    api_version=self.settings.azure_openai_api_version
                )
            elif self.settings.openai_api_key:
                return OpenAIEmbedding(api_key=self.settings.openai_api_key)
        except Exception as e:
            logger.warning(f"Failed to setup embedding model: {e}")
            return None
        return None

    async def evaluate(self, base_score: float, findings: List[RiskFinding], context: Dict[str, Any]) -> float:
        if not self.embed_model:
            return base_score # Fallback if no embedding model
            
        # Simplified logic: Compare evidence against a "standard" text
        # In a real system, we'd fetch the standard clause for the specific topic.
        # Here we mock the standard text to be generic safe legal text.
        
        standard_text = "The parties agree to reasonable terms and conditions regarding liability, termination, and data protection in accordance with industry standards."
        
        total_sim = 0.0
        count = 0
        
        for f in findings:
            if f.evidence and len(f.evidence) > 10:
                try:
                    # Get embeddings
                    std_emb = await self.embed_model.aget_text_embedding(standard_text)
                    clause_emb = await self.embed_model.aget_text_embedding(f.evidence)
                    
                    # Cosine similarity
                    sim = sum(a*b for a,b in zip(std_emb, clause_emb))
                    total_sim += sim
                    count += 1
                except Exception as e:
                    logger.warning(f"Embedding failed: {e}")
        
        avg_sim = total_sim / count if count > 0 else 1.0
        deviation = 1.0 - avg_sim
        
        # Policy: J_template = Base * (1 + 0.5 * Dev)
        adjusted_score = base_score * (1 + 0.5 * deviation)
        
        return min(100, max(0, adjusted_score))

class BayesJudge(ConsensusJudge):
    """Judge 3: Bayesian Anomaly Detector (Mocked History)"""
    
    def __init__(self):
        super().__init__("BayesJudge")
        # Mock historical stats (Mean, StdDev) per domain
        self.history = {
            "legal": (50, 15),
            "compliance": (40, 10),
            "financial": (45, 12),
            "operational": (35, 10),
            "security": (60, 20),
            "fraud": (20, 5)
        }

    async def evaluate(self, base_score: float, findings: List[RiskFinding], context: Dict[str, Any]) -> float:
        domain = context.get("domain", "legal").value.lower()
        mu, sigma = self.history.get(domain, (50, 15))
        
        # z-score
        epsilon = 1
        z = (base_score - mu) / (sigma + epsilon)
        
        # Anomaly score: min(1, max(0, 0.5 + 0.2 * |z|))
        anom = min(1.0, max(0.0, 0.5 + 0.2 * abs(z)))
        
        # Adjust: Base * (1 + Anom)
        # Note: If base is high, anomaly makes it higher (indicates it's unusually high or low).
        # Wait, policy says: J_bayes = Base * (1 + Anom).
        # If Base is 80 (High), and it's anomalous (z high), it boosts it even more?
        # Yes, high anomaly increases risk perception.
        
        adjusted_score = base_score * (1 + anom)
        return min(100, max(0, adjusted_score))

class LLMJudge(ConsensusJudge):
    """Judge 4: LLM Reasoner"""
    
    def __init__(self):
        super().__init__("LLMJudge")
        self.settings = get_settings()
        self.llm = self._setup_llm()
        
    def _setup_llm(self):
        try:
            if self.settings.azure_openai_api_key and self.settings.azure_openai_endpoint:
                 return AzureOpenAI(
                    model=self.settings.azure_openai_model,
                    deployment_name=self.settings.azure_openai_model,
                    api_key=self.settings.azure_openai_api_key,
                    azure_endpoint=self.settings.azure_openai_endpoint,
                    api_version=self.settings.azure_openai_api_version,
                    temperature=0.1
                )
            elif self.settings.openai_api_key:
                return OpenAI(
                    model="gpt-4o-mini",
                    api_key=self.settings.openai_api_key,
                    temperature=0.1
                )
        except Exception as e:
            logger.warning(f"Failed to setup LLM: {e}")
            return None
        return None

    async def evaluate(self, base_score: float, findings: List[RiskFinding], context: Dict[str, Any]) -> float:
        if not self.llm:
            return base_score
            
        # Construct summary of findings for LLM
        findings_text = "\n".join([f"- {f.parameter}: {f.finding} (Evidence: {f.evidence or 'None'})" for f in findings])
        
        prompt = f"""You are a senior legal counsel. Review these risk findings and the initial base score.
        
        Base Score: {base_score}
        
        Findings:
        {findings_text}
        
        Re-evaluate the risk from 0 (safe) to 100 (dangerous). Consider context, mitigations, and severity.
        Respond ONLY with a number between 0 and 100.
        """
        
        try:
            response = await self.llm.acomplete(prompt)
            text = str(response).strip()
            # Extract number
            import re
            match = re.search(r'\d+', text)
            if match:
                llm_val = int(match.group())
                llm_val = min(100, max(0, llm_val))
                
                # Policy: J_llm = 0.7 * LLM + 0.3 * Base
                final_score = 0.7 * llm_val + 0.3 * base_score
                return round(final_score, 2)
        except Exception as e:
            logger.warning(f"LLM Judge failed: {e}")
            
        return base_score
