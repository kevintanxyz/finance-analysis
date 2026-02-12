"""
LLM abstraction layer for WealthPoint.

Supports:
- Claude (Anthropic API) as primary LLM
- Ollama (local) as fallback

Factory function `create_llm()` returns the appropriate provider based on config.
"""
from abc import ABC, abstractmethod
from typing import Optional
from app.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion from system and user prompts.

        Args:
            system: System prompt (persona, instructions)
            user: User message
            response_format: Optional response format (e.g., "json")

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def complete_with_images(
        self,
        system: str,
        user: str,
        images_b64: list[str],
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion with image inputs (Claude Vision).

        Args:
            system: System prompt (persona, instructions)
            user: User message
            images_b64: List of base64-encoded images (PNG/JPEG)
            response_format: Optional response format (e.g., "json")

        Returns:
            Generated text response

        Raises:
            NotImplementedError: If provider doesn't support vision
        """
        pass


def create_llm() -> LLMProvider:
    """
    Create an LLM provider based on configuration.

    If ANTHROPIC_API_KEY is set, use Claude.
    Otherwise, use Ollama as fallback.
    """
    if settings.anthropic_api_key:
        from app.llm.claude import ClaudeProvider

        return ClaudeProvider(settings.anthropic_api_key)
    else:
        from app.llm.ollama import OllamaProvider

        return OllamaProvider(settings.ollama_model, settings.ollama_url)


__all__ = ["LLMProvider", "create_llm"]
