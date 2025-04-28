import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from functools import lru_cache
from typing import Optional, Dict, Any
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env file
env_path = find_dotenv()
if env_path:
    logger.info(f"Loading environment from {env_path}")
    load_dotenv(env_path)
else:
    logger.warning("No .env file found, using environment variables")

class Settings:
    # App
    APP_NAME: str = os.getenv("APP_NAME", "SemanticSQL")
    APP_VERSION: str = os.getenv("APP_VERSION", "0.1.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "t")
    
    # API settings
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    ALLOWED_HOSTS: list = json.loads(os.getenv("ALLOWED_HOSTS", '["*"]'))
    
    # Postgres DB
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "semanticsql")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    db_echo_log: bool = os.getenv("DB_ECHO_LOG", "False").lower() in ("true", "1", "t")
    
    # Qdrant Vector DB
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "semanticsql")
    
    # Connection pool settings
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme_in_production")
    
    # AI models
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.1"))
    
    # Vector embedding model
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
    
    # CORS settings
    CORS_ORIGINS: list = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]'))
    
    def __init__(self):
        # Validation
        if self.APP_ENV == "production" and self.SECRET_KEY == "changeme_in_production":
            logger.warning("Using default SECRET_KEY in production environment!")
        
        if not self.GEMINI_API_KEY and self.APP_ENV == "production":
            logger.warning("No GEMINI_API_KEY provided in production - AI features will not work!")

    @property
    def database_url(self) -> str:
        """Create database connection URL."""
        # Url encode password to handle special characters
        from urllib.parse import quote_plus
        password = quote_plus(self.POSTGRES_PASSWORD)
        
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        
    def dict(self) -> Dict[str, Any]:
        """Return dictionary representation of settings with secrets masked."""
        settings_dict = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        # Mask secrets
        for key in settings_dict:
            if any(secret in key.lower() for secret in ["password", "secret", "key", "token"]):
                settings_dict[key] = "***MASKED***"
        
        # Add properties
        settings_dict["database_url"] = "***MASKED***"
        
        return settings_dict

@lru_cache()
def get_settings() -> Settings:
    """Cached settings to avoid reloading."""
    return Settings()

settings = get_settings()

# Log application configuration (excluding secrets)
if settings.APP_DEBUG:
    logger.info(f"Application settings: {json.dumps(settings.dict(), indent=2)}")
else:
    logger.info(f"Application environment: {settings.APP_ENV}")
