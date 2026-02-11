"""
Ollama (local) provider.
"""
import httpx
from typing import Optional
from app.llm import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama local fallback provider."""

    def __init__(self, model: str = "llama3.1", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.

        Args:
            model: Ollama model name (default: llama3.1)
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url

    async def complete(
        self,
        system: str,
        user: str,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using Ollama.

        Args:
            system: System prompt
            user: User message
            response_format: Optional response format (not used by Ollama yet)

        Returns:
            Generated text response
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )

            response.raise_for_status()
            data = response.json()

            return data["message"]["content"]

    async def complete_with_images(
        self,
        system: str,
        user: str,
        images_b64: list[str],
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion with image inputs.

        NOTE: Ollama vision support is limited. This method is not yet implemented.

        Args:
            system: System prompt
            user: User message
            images_b64: List of base64-encoded images
            response_format: Optional response format

        Raises:
            NotImplementedError: Ollama vision not yet supported
        """
        raise NotImplementedError(
            "Ollama vision support not yet implemented. "
            "Use Claude (ANTHROPIC_API_KEY) for PDF vision extraction."
        )
