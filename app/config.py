"""
Application configuration using Pydantic Settings.

Environment variables are loaded from .env file.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    anthropic_api_key: Optional[str] = None
    ollama_model: str = "llama3.1"
    ollama_url: str = "http://localhost:11434"

    # Database
    database_url: str = "sqlite:///./wealthpoint.db"

    # API (simple auth v1)
    api_key: str = "your-api-key-here"

    # MCP Server
    mcp_transport: str = "stdio"  # stdio | streamable-http
    mcp_http_port: int = 3001

    # External MCP Servers (keys needed for Market Researcher)
    exa_api_key: Optional[str] = None
    bright_data_api_key: Optional[str] = None
    eodhd_api_key: Optional[str] = None

    # Market Data
    yfinance_cache_ttl: int = 300  # Cache 5 minutes

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
