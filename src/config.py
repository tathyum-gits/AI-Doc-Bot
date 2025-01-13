import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
import streamlit as st

# Load environment variables
load_dotenv()

@dataclass
class APIConfig:
    openai_api_key: str
    anthropic_api_key: str
    google_api_key: str
    
@dataclass
class VectorDBConfig:
    provider: str  # 'pinecone', 'faiss', or 'weaviate'
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    
@dataclass
class SecurityConfig:
    encryption_key: str
    session_expiry: int = 3600  # 1 hour
    
@dataclass
class AppConfig:
    api: APIConfig
    vector_db: VectorDBConfig
    security: SecurityConfig
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_file_types: list = None
    
    def __post_init__(self):
        if self.supported_file_types is None:
            self.supported_file_types = ['.pdf']

def get_secret(key: str, default: str = None) -> str:
    """Get secret from Streamlit secrets or environment variables."""
    try:
        return st.secrets[key]
    except (KeyError, AttributeError):
        return os.getenv(key, default)

def load_config() -> AppConfig:
    """Load and validate application configuration from secrets/environment."""
    
    # API Configuration
    api_config = APIConfig(
        openai_api_key=get_secret('OPENAI_API_KEY'),
        anthropic_api_key=get_secret('ANTHROPIC_API_KEY'),
        google_api_key=get_secret('GOOGLE_API_KEY')
    )
    
    # Vector DB Configuration
    vector_db_config = VectorDBConfig(
        provider=get_secret('VECTOR_DB_PROVIDER', 'faiss'),
        pinecone_api_key=get_secret('PINECONE_API_KEY'),
        pinecone_environment=get_secret('PINECONE_ENVIRONMENT')
    )
    
    # Security Configuration
    security_config = SecurityConfig(
        encryption_key=get_secret('ENCRYPTION_KEY'),
        session_expiry=int(get_secret('SESSION_EXPIRY', '3600'))
    )
    
    # Add deployment type check
    is_production = get_secret('DEPLOYMENT_ENV', 'dev').lower() == 'production'
    
    # Validate required configurations
    if is_production:
        if not api_config.openai_api_key:
            raise ValueError("OpenAI API key is required")
        if not api_config.anthropic_api_key:
            raise ValueError("Anthropic API key is required")
        if not api_config.google_api_key:
            raise ValueError("Google API key is required")
        if not security_config.encryption_key:
            raise ValueError("Encryption key is required")
    else:
        # In development, show warnings instead of raising errors
        if not api_config.openai_api_key:
            st.warning("OpenAI API key is missing")
        if not api_config.anthropic_api_key:
            st.warning("Anthropic API key is missing")
        if not api_config.google_api_key:
            st.warning("Google API key is missing")
        if not security_config.encryption_key:
            st.warning("Encryption key is missing")
    
    return AppConfig(
        api=api_config,
        vector_db=vector_db_config,
        security=security_config
    )

try:
    # Global configuration instance
    config = load_config()
except Exception as e:
    st.error(f"Configuration Error: {str(e)}")
    # Provide safe defaults if config fails
    config = AppConfig(
        api=APIConfig(
            openai_api_key="",
            anthropic_api_key="",
            google_api_key=""
        ),
        vector_db=VectorDBConfig(
            provider="faiss"
        ),
        security=SecurityConfig(
            encryption_key=get_secret('ENCRYPTION_KEY', 'dev-key-not-for-production')
        )
    )