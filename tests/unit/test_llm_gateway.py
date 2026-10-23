"""
Unit tests for Provider-Neutral LLM Gateway and Fallback Orchestration.
Simulates network timeouts, 401 unauthorized errors, 429 rate limits, and fallback recovery.
"""

from unittest.mock import MagicMock
import pytest
from src.llm.base_adapter import BaseLLMAdapter, LLMResponse, ProviderHealthStatus
from src.llm.mock_adapter import MockDeterministicAdapter
from src.llm.fallback_orchestrator import FallbackOrchestrator
from src.llm.openrouter_adapter import OpenRouterAdapter


class DummyWorkingAdapter(BaseLLMAdapter):
    def __init__(self, name="WorkingAdapter"):
        super().__init__(api_key="valid-key", model_id="dummy-v1")
        self._name = name

    def generate_text(self, prompt: str, system_prompt=None, timeout=15) -> LLMResponse:
        return LLMResponse(
            content=f"Response from {self._name}",
            provider_name=self._name,
            model_id=self.model_id,
            latency_seconds=0.1,
            is_fallback=False,
        )

    def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            provider_name=self._name,
            is_configured=True,
            is_healthy=True,
            message="OK",
        )


class DummyFailingAdapter(BaseLLMAdapter):
    def __init__(self, error_to_raise: Exception, name="FailingAdapter"):
        super().__init__(api_key="failing-key", model_id="dummy-fail")
        self.error_to_raise = error_to_raise
        self.call_count = 0
        self._name = name

    def generate_text(self, prompt: str, system_prompt=None, timeout=15) -> LLMResponse:
        self.call_count += 1
        raise self.error_to_raise

    def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            provider_name=self._name,
            is_configured=True,
            is_healthy=False,
            message=str(self.error_to_raise),
        )


def test_mock_deterministic_adapter_standalone():
    """Verify mock adapter generates valid grounded output offline."""
    mock_adapter = MockDeterministicAdapter()
    assert mock_adapter.is_configured is True
    res = mock_adapter.generate_text("Test prompt")
    assert isinstance(res, LLMResponse)
    assert res.provider_name == "MockDeterministic"
    assert "DETERMINISTIC" in res.content
    assert res.is_fallback is True

    health = mock_adapter.health_check()
    assert health.is_healthy is True


def test_base_adapter_is_configured_property():
    """Verify credential detection logic."""
    unconfigured = OpenRouterAdapter(api_key=None)
    assert unconfigured.is_configured is False

    short_key = OpenRouterAdapter(api_key="abc")
    assert short_key.is_configured is False

    valid_key = OpenRouterAdapter(api_key="mock_configured_test_key_12345")
    assert valid_key.is_configured is True


def test_orchestrator_success_on_primary():
    """Verify primary adapter is called and returned when healthy."""
    primary = DummyWorkingAdapter(name="Primary")
    secondary = DummyWorkingAdapter(name="Secondary")
    orchestrator = FallbackOrchestrator(adapters=[primary, secondary], max_retries=1)

    res = orchestrator.generate_with_fallback("Hello")
    assert res.provider_name == "Primary"
    assert res.is_fallback is False


def test_orchestrator_fail_fast_on_auth_error():
    """Verify 401 PermissionError fails fast without retrying and switches to secondary."""
    auth_fail = DummyFailingAdapter(
        error_to_raise=PermissionError("Invalid 401 token"), name="AuthFailing"
    )
    secondary = DummyWorkingAdapter(name="Secondary")
    orchestrator = FallbackOrchestrator(
        adapters=[auth_fail, secondary], max_retries=2, backoff_base=0.01
    )

    res = orchestrator.generate_with_fallback("Hello")
    # Must fail fast: call_count should be exactly 1 (no retries on 401)
    assert auth_fail.call_count == 1
    assert res.provider_name == "Secondary"
    assert res.is_fallback is True


def test_orchestrator_fallback_on_retryable_error():
    """Verify connection errors are retried up to max_retries before switching."""
    conn_fail = DummyFailingAdapter(
        error_to_raise=ConnectionError("503 Server Unavailable"), name="ConnFailing"
    )
    secondary = DummyWorkingAdapter(name="Secondary")
    orchestrator = FallbackOrchestrator(
        adapters=[conn_fail, secondary], max_retries=2, backoff_base=0.01
    )

    res = orchestrator.generate_with_fallback("Hello")
    # Initial attempt + 2 retries = 3 attempts
    assert conn_fail.call_count == 3
    assert res.provider_name == "Secondary"
    assert res.is_fallback is True


def test_orchestrator_all_external_failed_graceful_mock_degradation():
    """Verify when all external adapters fail, mock deterministic fallback is returned without error."""
    fail1 = DummyFailingAdapter(PermissionError("401"), name="Fail1")
    fail2 = DummyFailingAdapter(ConnectionError("Timeout"), name="Fail2")
    orchestrator = FallbackOrchestrator(adapters=[fail1, fail2], max_retries=1, backoff_base=0.01)

    res = orchestrator.generate_with_fallback("Hello")
    assert res.provider_name == "MockDeterministic"
    assert res.is_fallback is True
    assert "DETERMINISTIC" in res.content


def test_orchestrator_health_diagnostics():
    """Verify health diagnostics collect status across all configured adapters."""
    working = DummyWorkingAdapter(name="Working")
    failing = DummyFailingAdapter(ConnectionError("Down"), name="Failing")
    orchestrator = FallbackOrchestrator(adapters=[working, failing])

    statuses = orchestrator.check_all_adapters_health()
    assert len(statuses) == 2
    assert statuses[0].is_healthy is True
    assert statuses[1].is_healthy is False
