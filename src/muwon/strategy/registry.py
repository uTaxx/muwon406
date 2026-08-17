"""전략 가설을 등록하고 이름으로 찾아 쓰는 곳.

"가설을 검증하고 진화시킨다"는 걸 코드 흐름으로 풀면:
  1. 여기에 새 StrategyDefinition을 하나 추가한다(파라미터만 다르거나,
     아예 다른 Strategy 구현체일 수도 있다 — 둘 다 지원한다)
  2. scripts/run_hypothesis_sweep.py로 과거 데이터에 대해 백테스트하고
     결과를 DB(backtest_runs 테이블)에 남긴다
  3. 결과가 괜찮으면 SettingsService.set_active_strategy_key()로 "지금
     실거래에 쓸 키"만 바꾼다 — 코드 배포 없이 설정값 하나로 전환되고,
     이 변경 자체가 대시보드 "변경 이력"에 자동으로 남는다
  4. 실거래(TradingEngine/RealtimeTradingEngine)가 만든 매매 기록에도
     strategy_key가 찍혀서(trades 테이블), 나중에 "이 가설이 실전에서
     어떻게 됐는지"를 가설별로 나눠 볼 수 있다

status는 지금은 순수 메타데이터(코드가 강제하지 않음) — 사람이나 미래의
AI 제언이 "이건 아직 실험 중", "이건 검증 끝났다" 같은 걸 구분해 적어두는
용도다."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from muwon.domain.interfaces import Strategy
from muwon.strategy.rule_based import MovingAverageRsiParams, MovingAverageRsiStrategy


@dataclass(frozen=True)
class StrategyDefinition:
    key: str  # 고유 식별자 — trades/backtest_runs 테이블에 그대로 저장됨
    display_name: str
    description: str
    factory: Callable[[], Strategy]
    status: str = "hypothesis"  # "hypothesis" | "backtested" | "live" | "retired"


def _ma_rsi_default() -> Strategy:
    return MovingAverageRsiStrategy(MovingAverageRsiParams(), name="ma_rsi_v1")


def _ma_rsi_short_window_daytrade() -> Strategy:
    """단타용 가설: 일봉/분봉 모두에서 더 짧은 창으로 더 빠르게 반응하도록."""
    return MovingAverageRsiStrategy(
        MovingAverageRsiParams(sma_short=5, sma_long=20, rsi_period=7, volume_ma_window=5),
        name="ma_rsi_fast5_20",
    )


def _ma_rsi_looser_volume_filter() -> Strategy:
    """가설: 거래량 급증 기준을 완화하면(1.5배→1.2배) 진입 빈도가 늘어나는
    대신 승률이 떨어지는지 확인."""
    return MovingAverageRsiStrategy(
        MovingAverageRsiParams(volume_surge_ratio=1.2),
        name="ma_rsi_loose_volume",
    )


REGISTRY: list[StrategyDefinition] = [
    StrategyDefinition(
        key="ma_rsi_v1",
        display_name="이동평균+RSI (기본, 20/60/14)",
        description="20봉 골든크로스+거래량급증 또는 RSI 과매도반등 매수, 데드크로스/RSI 과매수 매도.",
        factory=_ma_rsi_default,
        status="live",
    ),
    StrategyDefinition(
        key="ma_rsi_fast5_20",
        display_name="이동평균+RSI 단타형 (5/20/7)",
        description="기본 전략과 같은 규칙, 창을 5/20/7로 좁혀 더 짧은 주기에 반응.",
        factory=_ma_rsi_short_window_daytrade,
        status="hypothesis",
    ),
    StrategyDefinition(
        key="ma_rsi_loose_volume",
        display_name="이동평균+RSI 거래량필터 완화",
        description="거래량 급증 기준을 1.5배→1.2배로 낮춰 진입 빈도/승률 트레이드오프 확인.",
        factory=_ma_rsi_looser_volume_filter,
        status="hypothesis",
    ),
]


def get_definition(key: str) -> StrategyDefinition:
    for definition in REGISTRY:
        if definition.key == key:
            return definition
    known = ", ".join(d.key for d in REGISTRY)
    raise KeyError(f"등록되지 않은 전략 키: '{key}' (등록된 키: {known})")


def build_strategy(key: str) -> Strategy:
    return get_definition(key).factory()


def list_definitions() -> list[StrategyDefinition]:
    return list(REGISTRY)
