"""
Google Gemini Provider Adapter.
Implements Google Gemini REST API interface.
"""

import time
from typing import Optional
import requests
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus
from src.utils.logger import logger


class GeminiAdapter(BaseLLMAdapter):
    """Adapter for routing requests to Google Gemini REST endpoint."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: Optional[str] = None, model_id: str = "gemini-1.5-flash"):
        super().__init__(api_key=api_key, model_id=model_id)

    def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None, timeout: int = 15
    ) -> LLMResponse:
        if not self.is_configured:
            raise ValueError("Google Gemini API key is not configured")

        url = f"{self.BASE_URL}/{self.model_id}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        t0 = time.time()
        logger.debug("Dispatching request to Google Gemini model: %s", self.model_id)
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - t0

        if response.status_code in [401, 403]:
            raise PermissionError(f"Gemini authentication error ({response.status_code}): Invalid or unauthorized API key")
        elif response.status_code == 429:
            raise ConnectionError("Gemini rate limit or quota exceeded (429)")
        elif response.status_code >= 400:
            raise ConnectionError(f"Gemini HTTP {response.status_code}: {response.text}")

        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as err:
            raise ValueError(f"Malformed Gemini response payload: {err}")

        usage = data.get("usageMetadata")

        return LLMResponse(
            content=content,
            provider_name="Gemini",
            model_id=self.model_id,
            latency_seconds=round(elapsed, 2),
            token_usage=usage,
            is_fallback=False,
        )

    def health_check(self) -> ProviderHealthStatus:
        if not self.is_configured:
            return ProviderHealthStatus(
                provider_name="Gemini",
                is_configured=False,
                is_healthy=False,
                message="API key not provided in environment.",
            )

        try:
            res = self.generate_text("Respond with 'OK'.", timeout=8)
            return ProviderHealthStatus(
                provider_name="Gemini",
                is_configured=True,
                is_healthy=True,
                message="Connected and authenticated successfully.",
                latency_ms=round(res.latency_seconds * 1000.0, 1),
            )
        except Exception as e:
            return ProviderHealthStatus(
                provider_name="Gemini",
                is_configured=True,
                is_healthy=False,
                message=f"Health probe failed: {str(e)}",
            )
