"""
Configuration settings for the Contract Risk Analysis Platform.
Loads environment variables and provides typed configuration objects.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from functools import lru_cache
from typing import List, Union
import os
from urllib.parse import quote_plus


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    app_name: str = Field(default="Contract Risk Analyzer")
    app_version: str = Field(default="1.0.0")
    debug: Union[bool, str] = Field(default=True)
    
    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="contract_risk_analyzer")
    mongodb_username: str = Field(default="")
    mongodb_password: str = Field(default="")
    mongodb_host: str = Field(default="")
    mongodb_use_srv: bool = Field(default=False)
    
    # Azure OpenAI
    azure_openai_api_key: str = Field(default="")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_URL")
    azure_openai_api_version: str = Field(default="2024-05-01-preview")
    azure_openai_model: str = Field(default="gpt-4o", alias="AZURE_OPENAI_MODEL") 
    azure_embedding_model: str = Field(default="text-embedding-3-small", alias="AZURE_EMBEDDING_MODEL")

    # OpenAI (Legacy/Fallback)
    openai_api_key: str = Field(default="")
    
    # Upload settings
    max_file_size_mb: int = Field(default=50)
    allowed_extensions: str = Field(default="pdf,docx,xlsx")
    upload_dir: str = Field(default="uploads")
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    

    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        """Assemble database connection string if components are provided."""
        if self.mongodb_host and self.mongodb_username and self.mongodb_password:
            protocol = "mongodb+srv" if self.mongodb_use_srv else "mongodb"
            username = quote_plus(self.mongodb_username)
            password = quote_plus(self.mongodb_password)
            self.mongodb_url = f"{protocol}://{username}:{password}@{self.mongodb_host}"
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False



# Risk domain weights for overall score calculation
RISK_DOMAIN_WEIGHTS = {
    "legal": 0.25,
    "compliance": 0.20,
    "financial": 0.20,
    "operational": 0.10,
    "security": 0.15,
    "fraud": 0.10
}

# Risk level thresholds
RISK_LEVELS = {
    "low": (0, 25),
    "medium": (26, 50),
    "high": (51, 75),
    "critical": (76, 100)
}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
