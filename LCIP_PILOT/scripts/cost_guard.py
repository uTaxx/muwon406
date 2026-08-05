#!/usr/bin/env python3
"""TASK-015 — Cost Guard.

월 누적 Claude API 비용을 판정해 70/90/100% 단계별 통제 상태를 반환하는 순수 함수 위주 모듈.
실제 Google Sheets(COST_LOG) 연동은 TASK-008 이후 라운드에서 연결한다 — 이번 라운드는 로직만
로컬에서 테스트 가능하게 구현한다 (config/cost_policy.yaml 값을 사용).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from _common import load_yaml

CostState = Literal["NORMAL", "WARNING", "RESTRICTED", "STOPPED"]


@dataclass(frozen=True)
class CostGuardResult:
    state: CostState
    cumulative_usd: float
    budget_usd: float
    rate: float
    allow_deep_analysis: bool
    allow_emergency_only: bool
    message: str


def load_cost_policy() -> dict:
    return load_yaml("config/cost_policy.yaml")["cost"]


def estimate_cost_usd(
    input_tokens: int,
    output_tokens: int,
    usd_per_million_input: float,
    usd_per_million_output: float,
) -> float:
    """모델별 단가(config/model_pricing.yaml에서 로드)로 1회 호출 비용을 계산한다."""
    return (input_tokens / 1_000_000) * usd_per_million_input + (
        output_tokens / 1_000_000
    ) * usd_per_million_output


def evaluate(cumulative_usd: float, policy: dict | None = None) -> CostGuardResult:
    """월 누적 비용을 받아 현재 통제 단계를 판정한다.

    policy는 기본적으로 config/cost_policy.yaml에서 로드하지만, 테스트에서는 fixture를
    직접 넘길 수 있다.
    """
    policy = policy or load_cost_policy()
    budget = float(policy["monthly_budget_usd"])
    rate = cumulative_usd / budget if budget else 0.0

    if rate >= policy["hard_stop_rate"]:
        return CostGuardResult(
            state="STOPPED",
            cumulative_usd=cumulative_usd,
            budget_usd=budget,
            rate=rate,
            allow_deep_analysis=False,
            allow_emergency_only=False,
            message=f"월 예산 {policy['hard_stop_rate']*100:.0f}% 도달 — Claude API 호출을 중지한다.",
        )
    if rate >= policy["restrict_rate"]:
        return CostGuardResult(
            state="RESTRICTED",
            cumulative_usd=cumulative_usd,
            budget_usd=budget,
            rate=rate,
            allow_deep_analysis=True,
            allow_emergency_only=True,
            message=f"월 예산 {policy['restrict_rate']*100:.0f}% 도달 — 긴급 건만 심층분석을 허용한다.",
        )
    if rate >= policy["warning_rate"]:
        return CostGuardResult(
            state="WARNING",
            cumulative_usd=cumulative_usd,
            budget_usd=budget,
            rate=rate,
            allow_deep_analysis=True,
            allow_emergency_only=False,
            message=f"월 예산 {policy['warning_rate']*100:.0f}% 도달 — 관리자 경고.",
        )
    return CostGuardResult(
        state="NORMAL",
        cumulative_usd=cumulative_usd,
        budget_usd=budget,
        rate=rate,
        allow_deep_analysis=True,
        allow_emergency_only=False,
        message="정상 범위.",
    )


def check_daily_deep_analysis_limit(
    today_deep_analysis_count: int, policy: dict | None = None
) -> bool:
    """오늘 이미 수행한 심층분석 건수가 일일 상한 미만이면 True."""
    policy = policy or load_cost_policy()
    return today_deep_analysis_count < policy["daily_deep_analysis_limit"]


def main() -> int:
    policy = load_cost_policy()
    print("=== Cost Guard 로컬 점검 (실제 COST_LOG 연동은 TASK-008 이후) ===")
    for pct in (0.0, 0.5, 0.70, 0.90, 1.00, 1.10):
        cumulative = policy["monthly_budget_usd"] * pct
        result = evaluate(cumulative, policy)
        print(f"  누적 {cumulative:.2f} USD ({pct*100:.0f}%) -> {result.state}: {result.message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
