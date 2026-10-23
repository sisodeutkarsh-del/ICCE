"""
Hugging Face Inference Provider Adapter.
Implements Hugging Face Serverless Inference API interface.
"""

import time
from typing import Optional
import requests
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus
from src.utils.logger import logger


class HuggingFaceAdapter(BaseLLMAdapter):
    """Adapter for routing requests to Hugging Face serverless inference."""

    BASE_URL = "https://api-inference.huggingface.co/models"

    def __init__(self, api_key: Optional[str] = None, model_id: str = "mistralai/Mistral-7B-Instruct-v0.3"):
        super().__init__(api_key=api_key, model_id=model_id)

    def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None, timeout: int = 15
    ) -> LLMResponse:
        if not self.is_configured:
            raise ValueError("Hugging Face API key is not configured")

        url = f"{self.BASE_URL}/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
        payload = {
            "inputs": full_prompt,
            "parameters": {"max_new_tokens": 512, "temperature": 0.2, "return_full_text": False},
        }

        t0 = time.time()
        logger.debug("Dispatching request to Hugging Face model: %s", self.model_id)
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - t0

        if response.status_code == 401:
            raise PermissionError("Hugging Face authentication failed (401): Invalid user token")
        elif response.status_code == 429:
            raise ConnectionError("Hugging Face rate limit exceeded (429)")
        elif response.status_code == 503:
            raise ConnectionError("Hugging Face model is currently loading (503), retryable")
        elif response.status_code >= 400:
            raise ConnectionError(f"Hugging Face HTTP {response.status_code}: {response.text}")

        data = response.json()
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            content = data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            content = data["generated_text"]
        else:
            content = str(data)

        return LLMResponse(
            content=content.strip(),
            provider_name="HuggingFace",
            model_id=self.model_id,
            latency_seconds=round(elapsed, 2),
            token_usage=None,
            is_fallback=False,
        )

    def health_check(self) -> ProviderHealthStatus:
        if not self.is_configured:
            return ProviderHealthStatus(
                provider_name="HuggingFace",
                is_configured=False,
                is_healthy=False,
                message="API key not provided in environment.",
            )

        try:
            res = self.generate_text("Hi", timeout=8)
            return ProviderHealthStatus(
                provider_name="HuggingFace",
                is_configured=True,
                is_healthy=True,
                message="Connected and authenticated successfully.",
                latency_ms=round(res.latency_seconds * 1000.0, 1),
            )
        except Exception as e:
            return ProviderHealthStatus(
                provider_name="HuggingFace",
                is_configured=True,
                is_healthy=False,
                message=f"Health probe failed: {str(e)}",
            )
