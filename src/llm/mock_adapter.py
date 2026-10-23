"""
Deterministic Mock LLM Adapter.
Provides 100% offline, reproducible fallback synthesis without external API calls or keys.
"""

import time
from typing import Optional
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus


class MockDeterministicAdapter(BaseLLMAdapter):
    """Deterministic offline adapter guaranteeing continuous operation without internet or keys."""

    def __init__(self, model_id: str = "deterministic-rule-engine-v1"):
        super().__init__(api_key="mock-offline-key", model_id=model_id)

    @property
    def is_configured(self) -> bool:
        return True

    def generate_text(
        self, prompt: str, system_prompt: Optional[str] = None, timeout: int = 15
    ) -> LLMResponse:
        t0 = time.time()
        
        # Grounded template response acknowledging deterministic offline execution
        content = (
            "[DETERMINISTIC AGENT SYNTHESIS - OFFLINE FALLBACK MODE]\n\n"
            "Executive Summary:\n"
            "Based on the technical compatibility criteria for Pune City rooftop solar projects under MSEDCL net-metering guidelines, "
            "candidate partners were screened across technology match, capacity feasibility, India service presence, and BIS/IEC compliance.\n\n"
            "Key Recommendation Insight:\n"
            "Providers with direct Indian subsidiaries and local Maharashtra channel partners offer superior long-term warranty security "
            "and faster service turnaround (SLA < 48h) for Pune's urban rooftop environments.\n\n"
            "Note: This analysis was generated deterministically by the local agent engine without external cloud LLM dependencies."
        )
        elapsed = time.time() - t0

        return LLMResponse(
            content=content,
            provider_name="MockDeterministic",
            model_id=self.model_id,
            latency_seconds=round(elapsed, 4),
            token_usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(content.split())},
            is_fallback=True,
        )

    def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            provider_name="MockDeterministic",
            is_configured=True,
            is_healthy=True,
            message="Offline deterministic fallback engine is fully active and ready.",
            latency_ms=0.1,
        )
