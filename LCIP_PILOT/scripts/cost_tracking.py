"""TASK-015 연동 — Provider(AIProvider) 사용량을 Cost Guard와 연결한다.

Round 4 지시: "Cost Guard를 Provider 사용량 추적과 연동한다." `providers/*.py`가 반환하는
`ProviderUsage`(input/output 토큰)를 `config/model_pricing.yaml` 단가로 환산해 누적 비용을
계산하고, `cost_guard.evaluate()`로 현재 통제 단계를 판정한다.

`config/model_pricing.yaml`의 단가가 아직 TODO placeholder(0.0)인 동안은 실제 비용도 항상
0으로 계산된다 — 이는 버그가 아니라 "실제 모델 단가가 확정되지 않았다"는 사실을 정직하게
반영한 것이다(CLAUDE.md 절대 원칙 #8, 임의 추정 금지).

Round 5 Technical Debt 정리: `config/model_pricing.yaml`의 키를 `config/model_registry.yaml`
의 tier 키(classification/deep_analysis/future)와 동일하게 맞춰서, Round 4까지 있던
tier→pricing 키 매핑 테이블(TIER_TO_PRICING_KEY)을 제거했다 — `purpose`를 그대로 pricing
조회 키로 쓴다.
"""
from __future__ import annotations

import cost_guard
from _common import load_yaml
from providers.base import ProviderUsage


def load_pricing_registry() -> dict:
    return load_yaml("config/model_pricing.yaml")["pricing"]


def estimate_usage_cost_usd(
    usage: ProviderUsage, purpose: str, pricing_registry: dict | None = None
) -> float:
    """purpose(classification/deep_analysis/future)별 단가로 1회 Provider 호출 비용(USD)을
    계산한다. purpose는 config/model_registry.yaml의 tier 키와 동일하다."""
    pricing_registry = pricing_registry if pricing_registry is not None else load_pricing_registry()
    if purpose not in pricing_registry:
        raise ValueError(
            f"'{purpose}'에 대한 단가 정보가 없다 — config/model_pricing.yaml을 확인해야 한다."
        )
    unit = pricing_registry[purpose]
    return cost_guard.estimate_cost_usd(
        usage.input_tokens,
        usage.output_tokens,
        unit["usd_per_million_input_tokens"],
        unit["usd_per_million_output_tokens"],
    )


def track_provider_calls(
    calls: list[tuple[ProviderUsage, str]], pricing_registry: dict | None = None
) -> float:
    """[(usage, purpose), ...] 형태의 여러 Provider 호출 누적 비용(USD)을 합산한다."""
    return sum(
        estimate_usage_cost_usd(usage, purpose, pricing_registry) for usage, purpose in calls
    )


def evaluate_after_calls(
    calls: list[tuple[ProviderUsage, str]],
    prior_cumulative_usd: float = 0.0,
    pricing_registry: dict | None = None,
    policy: dict | None = None,
) -> cost_guard.CostGuardResult:
    """이번 라운드 호출들의 비용을 기존 누적액에 더해 Cost Guard 상태를 재판정한다."""
    new_cost = track_provider_calls(calls, pricing_registry)
    return cost_guard.evaluate(prior_cumulative_usd + new_cost, policy)
