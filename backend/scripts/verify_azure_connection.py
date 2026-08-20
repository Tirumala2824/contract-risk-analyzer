
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import backend modules
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from backend.config import get_settings
from backend.services.agents import AgentFactory
from backend.models import RiskDomain

async def verify_azure_setup():
    """Verify Azure OpenAI setup."""
    print("Verifying Azure OpenAI Configuration...")
    settings = get_settings()
    
    print(f"API Type: Azure OpenAI")
    print(f"Endpoint: {settings.azure_openai_endpoint}")
    print(f"Model: {settings.azure_openai_model}")
    print(f"Embedding Model: {settings.azure_embedding_model}")
    print(f"API Version: {settings.azure_openai_api_version}")
    
    if not settings.azure_openai_api_key:
        print("❌ Error: AZURE_OPENAI_API_KEY is not set.")
        return

    try:
        # Initialize an agent (this triggers _setup_llm)
        print("\nInitializing Legal Risk Agent...")
        agent = AgentFactory.get_agent(RiskDomain.LEGAL)
        
        if not agent.llm:
            print("❌ Error: LLM not initialized. Check logs/configuration.")
            return

        print("✅ Agent initialized successfully.")
        
        # Test Completion
        print("\nTesting LLM Completion...")
        response = agent.llm.complete("Hello, are you ready to analyze contracts?")
        print(f"✅ LLM Response: {response}")

        # Test Embedding
        print("\nTesting Embedding...")
        embedding = agent.embed_model.get_text_embedding("Contract analysis start.")
        print(f"✅ Embedding generated (length: {len(embedding)})")
        
        print("\n🎉 Azure OpenAI Verification Successful!")

    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_azure_setup())
