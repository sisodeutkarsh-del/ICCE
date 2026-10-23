"""
OpenRouter Provider Adapter.
Implements OpenRouter OpenAI-compatible chat completion endpoint.
"""

import time
from typing import Optional
import requests
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus
from src.utils.logger import logger


class OpenRouterAdapter(BaseLLMAdapter):
    """Adapter for routing requests to OpenRouter models."""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model_id: str = "meta-llama/llama-3.1-8b-instruct:free"):
        super().__init__(api_key=api_key, model_id=model_id)

    def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None, timeout: int = 15
    ) -> LLMResponse:
        if not self.is_configured:
            raise ValueError("OpenRouter API key is not configured")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Pune Solar Partner Matcher",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        t0 = time.time()
        logger.debug("Dispatching request to OpenRouter model: %s", self.model_id)
        response = requests.post(self.ENDPOINT, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - t0

        if response.status_code == 401:
            raise PermissionError("OpenRouter authentication failed: invalid API key (401)")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "5")
            raise ConnectionError(f"OpenRouter rate limit reached (429). Retry-After: {retry_after}s")
        elif response.status_code >= 400:
            raise ConnectionError(f"OpenRouter HTTP {response.status_code}: {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage")

        return LLMResponse(
            content=content,
            provider_name="OpenRouter",
            model_id=self.model_id,
            latency_seconds=round(elapsed, 2),
            token_usage=usage,
            is_fallback=False,
        )

    def health_check(self) -> ProviderHealthStatus:
        if not self.is_configured:
            return ProviderHealthStatus(
                provider_name="OpenRouter",
                is_configured=False,
                is_healthy=False,
                message="API key not provided in environment.",
            )

        try:
            # Send a minimal test probe
            res = self.generate_text("Respond with 'OK'.", timeout=8)
            return ProviderHealthStatus(
                provider_name="OpenRouter",
                is_configured=True,
                is_healthy=True,
                message="Connected and authenticated successfully.",
                latency_ms=round(res.latency_seconds * 1000.0, 1),
            )
        except Exception as e:
            return ProviderHealthStatus(
                provider_name="OpenRouter",
                is_configured=True,
                is_healthy=False,
                message=f"Health probe failed: {str(e)}",
            )
