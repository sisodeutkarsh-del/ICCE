"""
Fallback Orchestration Gateway.
Manages adapter priority order, bounded retries, rate-limit backoff,
fail-fast on authentication errors, and graceful degradation to offline deterministic synthesis.
"""

import time
from typing import List, Optional
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus
from src.llm.mock_adapter import MockDeterministicAdapter
from src.utils.logger import logger


class FallbackOrchestrator:
    """Orchestrates resilient LLM calls across multiple provider adapters."""

    def __init__(
        self,
        adapters: List[BaseLLMAdapter],
        max_retries: int = 2,
        backoff_base: float = 1.0,
        default_timeout: int = 15,
    ):
        self.adapters = adapters
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.default_timeout = default_timeout
        self.fallback_mock = MockDeterministicAdapter()

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> LLMResponse:
        """
        Attempts generation using configured adapters in sequential priority.
        Falls back to next adapter upon retryable failure or authentication failure.
        Always terminates cleanly on MockDeterministicAdapter if all external providers fail.
        """
        req_timeout = timeout or self.default_timeout

        # Filter for configured adapters
        candidates = [a for a in self.adapters if a.is_configured]

        if not candidates:
            logger.info("No external LLM providers configured. Utilizing deterministic offline fallback.")
            return self.fallback_mock.generate_text(prompt, system_prompt, timeout=req_timeout)

        for adapter_idx, adapter in enumerate(candidates):
            adapter_name = adapter.__class__.__name__
            for attempt in range(self.max_retries + 1):
                try:
                    logger.debug(
                        "Attempting call via %s (attempt %d/%d)",
                        adapter_name, attempt + 1, self.max_retries + 1
                    )
                    response = adapter.generate_text(prompt, system_prompt, timeout=req_timeout)
                    if adapter_idx > 0:
                        response.is_fallback = True
                    return response

                except PermissionError as pe:
                    # Authentication or permission error (401/403): DO NOT RETRY. Fail fast.
                    logger.warning(
                        "Authentication failed on %s: %s. Failing fast to next configured provider.",
                        adapter_name, str(pe)
                    )
                    break

                except (ConnectionError, TimeoutError, Exception) as err:
                    logger.warning(
                        "Retryable error on %s (attempt %d/%d): %s",
                        adapter_name, attempt + 1, self.max_retries + 1, str(err)
                    )
                    if attempt < self.max_retries:
                        backoff = min(self.backoff_base * (2 ** attempt), 4.0)
                        logger.info("Backing off for %.2fs before retry...", backoff)
                        time.sleep(backoff)
                    else:
                        logger.warning("Exhausted retries for %s. Transitioning to next adapter.", adapter_name)
                        break

        # All external adapters failed -> Graceful deterministic degradation
        logger.warning("All configured external LLM adapters failed. Engaging deterministic offline engine.")
        fallback_res = self.fallback_mock.generate_text(prompt, system_prompt, timeout=req_timeout)
        fallback_res.is_fallback = True
        return fallback_res

    def check_all_adapters_health(self) -> List[ProviderHealthStatus]:
        """Runs health diagnostics across all managed adapters."""
        statuses = []
        for a in self.adapters:
            try:
                st = a.health_check()
                statuses.append(st)
            except Exception as e:
                statuses.append(
                    ProviderHealthStatus(
                        provider_name=a.__class__.__name__,
                        is_configured=a.is_configured,
                        is_healthy=False,
                        message=f"Health probe error: {str(e)}",
                    )
                )
        return statuses
