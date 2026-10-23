"""
Base abstractions for Provider-Neutral LLM Gateway.
Defines interfaces, response wrappers, and health check types.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider adapter."""
    content: str = Field(..., description="Generated text content")
    provider_name: str = Field(..., description="Adapter name (e.g. OpenRouter, Gemini, HuggingFace, Mock)")
    model_id: str = Field(..., description="Underlying model identifier")
    latency_seconds: float = Field(..., description="Round-trip execution latency in seconds")
    token_usage: Optional[Dict[str, int]] = Field(default=None, description="Prompt/completion token counts if reported")
    is_fallback: bool = Field(default=False, description="True if response came from an automated fallback")


class ProviderHealthStatus(BaseModel):
    """Health status and diagnostic metadata for a model provider."""
    provider_name: str = Field(..., description="Name of the provider adapter")
    is_configured: bool = Field(..., description="True if API key or endpoint is configured")
    is_healthy: bool = Field(..., description="True if health probe or ping succeeded")
    message: str = Field(..., description="Informational message or reason for failure")
    latency_ms: Optional[float] = Field(default=None, description="Latency in milliseconds if measured")


class BaseLLMAdapter(ABC):
    """Abstract base adapter that all LLM providers must implement."""

    def __init__(self, api_key: Optional[str] = None, model_id: str = ""):
        self.api_key = api_key
        self.model_id = model_id

    @property
    def is_configured(self) -> bool:
        """Returns True if the adapter has valid credential tokens."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: int = 15,
    ) -> LLMResponse:
        """Executes a text generation request with bounded timeout."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealthStatus:
        """Performs a lightweight probe to verify connectivity and credentials."""
        pass
