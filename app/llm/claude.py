"""
Claude (Anthropic API) provider.
"""
import anthropic
from typing import Optional
from app.llm import LLMProvider


class ClaudeProvider(LLMProvider):
    """Anthropic Claude via API."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model ID (default: Sonnet 4.5)
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(
        self,
        system: str,
        user: str,
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using Claude.

        Args:
            system: System prompt
            user: User message
            response_format: Optional response format (not used by Claude API yet)

        Returns:
            Generated text response
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        # Extract text content
        return response.content[0].text

    async def complete_with_images(
        self,
        system: str,
        user: str,
        images_b64: list[str],
        response_format: Optional[str] = None,
    ) -> str:
        """
        Generate a completion with image inputs using Claude Vision.

        Args:
            system: System prompt
            user: User message
            images_b64: List of base64-encoded images (PNG/JPEG)
            response_format: Optional response format ("json" for structured output)

        Returns:
            Generated text response
        """
        # Build content with images
        content_blocks = []

        # Add all images first
        for img_b64 in images_b64:
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",  # PDF pages rendered as PNG
                    "data": img_b64,
                },
            })

        # Add text prompt after images
        content_blocks.append({
            "type": "text",
            "text": user,
        })

        # Call Claude with vision-capable model
        response = await self.client.messages.create(
            model=self.model,  # Claude Sonnet/Opus support vision
            max_tokens=8192,  # More tokens for structured extraction
            system=system,
            messages=[{"role": "user", "content": content_blocks}],
        )

        # Extract text content
        return response.content[0].text
