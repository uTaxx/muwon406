import pytest

import cost_tracking
from providers.base import ProviderUsage

PRICING = {
    "classification": {
        "usd_per_million_input_tokens": 1.0,
        "usd_per_million_output_tokens": 5.0,
    },
    "deep_analysis": {
        "usd_per_million_input_tokens": 3.0,
        "usd_per_million_output_tokens": 15.0,
    },
}

POLICY = {
    "monthly_budget_usd": 20,
    "target_budget_usd": 15,
    "warning_rate": 0.70,
    "restrict_rate": 0.90,
    "hard_stop_rate": 1.00,
    "daily_deep_analysis_limit": 5,
}


def test_estimate_usage_cost_for_classification_tier():
    usage = ProviderUsage(input_tokens=1_000_000, output_tokens=1_000_000, model="mock-classifier")
    cost = cost_tracking.estimate_usage_cost_usd(usage, "classification", PRICING)
    assert cost == 6.0  # 1.0 + 5.0


def test_estimate_usage_cost_for_deep_analysis_tier():
    usage = ProviderUsage(input_tokens=1_000_000, output_tokens=1_000_000, model="mock-analyzer")
    cost = cost_tracking.estimate_usage_cost_usd(usage, "deep_analysis", PRICING)
    assert cost == 18.0  # 3.0 + 15.0


def test_estimate_usage_cost_unknown_purpose_raises():
    usage = ProviderUsage(input_tokens=100, output_tokens=100, model="x")
    with pytest.raises(ValueError):
        cost_tracking.estimate_usage_cost_usd(usage, "unknown_purpose", PRICING)


def test_track_provider_calls_sums_multiple_calls():
    calls = [
        (ProviderUsage(1_000_000, 1_000_000, "mock-classifier"), "classification"),
        (ProviderUsage(1_000_000, 1_000_000, "mock-analyzer"), "deep_analysis"),
    ]
    assert cost_tracking.track_provider_calls(calls, PRICING) == 24.0


def test_evaluate_after_calls_reaches_warning_state():
    calls = [(ProviderUsage(1_000_000, 1_000_000, "mock-analyzer"), "deep_analysis")]  # 18.0
    result = cost_tracking.evaluate_after_calls(
        calls, prior_cumulative_usd=0.0, pricing_registry=PRICING, policy=POLICY
    )
    assert result.state == "RESTRICTED"  # 18/20 = 90%


def test_evaluate_after_calls_with_placeholder_pricing_is_zero_cost():
    """실제 model_pricing.yaml은 아직 TODO(0.0)이므로, 명시적으로 넘기지 않으면 비용이
    0으로 계산되어야 한다 — 모델 단가 미확정 상태를 정직하게 반영한다."""
    calls = [(ProviderUsage(1_000_000, 1_000_000, "mock-classifier"), "classification")]
    cost = cost_tracking.track_provider_calls(calls)  # loads real config/model_pricing.yaml
    assert cost == 0.0
