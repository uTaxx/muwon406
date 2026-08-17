"""전략 가설을 등록하고 이름으로 찾아 쓰는 곳.

"가설을 검증하고 진화시킨다"는 걸 코드 흐름으로 풀면:
  1. 여기에 새 StrategyDefinition을 하나 추가한다(파라미터만 다르거나,
     아예 다른 Strategy 구현체일 수도 있다 — 둘 다 지원한다)
  2. scripts/run_hypothesis_sweep.py로 과거 데이터에 대해 백테스트하고
     결과를 DB(backtest_runs 테이블)에 남긴다
  3. 결과가 괜찮으면 대시보드나 configure.py로 "지금 실거래에 쓸 키"만
     바꾼다 — 코드 배포 없이 설정값 하나로 전환되고, 이 변경 자체가
     대시보드 "변경 이력"에 자동으로 남는다
  4. 실거래(TradingEngine/RealtimeTradingEngine)가 만든 매매 기록에도
     strategy_key가 찍혀서(trades 테이블), 나중에 "이 가설이 실전에서
     어떻게 됐는지"를 가설별로 나눠 볼 수 있다

category는 전략의 성격(추세추종/평균회귀/돌파/복합)을 나타낸다 — 계열이
다르면 잘 맞는 시장 국면도 다르므로, 대시보드에서 계열별로 묶어 보면
"지금 장에는 어떤 계열이 통하는가"를 읽을 수 있다.

status는 순수 메타데이터(코드가 강제하지 않음) — 사람이나 미래의 AI 제언이
"이건 아직 실험 중", "이건 검증 끝났다" 같은 걸 구분해 적어두는 용도다."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from muwon.domain.interfaces import Strategy
from muwon.strategy.breakout import (
    BollingerBreakoutParams,
    BollingerBreakoutStrategy,
    PriceChannelBreakoutStrategy,
    PriceChannelParams,
    VolumeSurgeParams,
    VolumeSurgeStrategy,
)
from muwon.strategy.reversion import (
    BollingerReversionParams,
    BollingerReversionStrategy,
    RsiReversionParams,
    RsiReversionStrategy,
    StochasticParams,
    StochasticStrategy,
)
from muwon.strategy.rule_based import MovingAverageRsiParams, MovingAverageRsiStrategy
from muwon.strategy.trend import (
    DonchianBreakoutParams,
    DonchianBreakoutStrategy,
    EmaCrossParams,
    EmaCrossStrategy,
    GoldenCrossParams,
    GoldenCrossStrategy,
    MacdCrossParams,
    MacdCrossStrategy,
)

CATEGORY_TREND = "추세추종"
CATEGORY_REVERSION = "평균회귀"
CATEGORY_BREAKOUT = "돌파·모멘텀"
CATEGORY_HYBRID = "복합"

CATEGORIES = [CATEGORY_TREND, CATEGORY_REVERSION, CATEGORY_BREAKOUT, CATEGORY_HYBRID]


@dataclass(frozen=True)
class StrategyDefinition:
    key: str  # 고유 식별자 — trades/backtest_runs 테이블에 그대로 저장됨
    display_name: str
    description: str
    factory: Callable[[], Strategy]
    category: str = CATEGORY_HYBRID
    status: str = "hypothesis"  # "hypothesis" | "backtested" | "live" | "retired"


REGISTRY: list[StrategyDefinition] = [
    # ── 복합: 이동평균 추세 + RSI 반등을 한 전략에 섞은 것 (이 프로젝트의 출발점) ──
    StrategyDefinition(
        key="ma_rsi_v1",
        display_name="이동평균+RSI 복합 (20/60/14)",
        description="단기선 상향돌파+거래량급증 또는 RSI 과매도반등 매수, 단기선 하향이탈/RSI 과매수 매도.",
        factory=lambda: MovingAverageRsiStrategy(MovingAverageRsiParams(), name="ma_rsi_v1"),
        category=CATEGORY_HYBRID,
        status="live",
    ),
    StrategyDefinition(
        key="ma_rsi_fast5_20",
        display_name="이동평균+RSI 단타형 (5/20/7)",
        description="같은 규칙, 창을 5/20/7로 좁혀 더 짧은 주기에 반응. 신호가 잦아지는 대신 헛신호도 늘어난다.",
        factory=lambda: MovingAverageRsiStrategy(
            MovingAverageRsiParams(sma_short=5, sma_long=20, rsi_period=7, volume_ma_window=5),
            name="ma_rsi_fast5_20",
        ),
        category=CATEGORY_HYBRID,
    ),
    StrategyDefinition(
        key="ma_rsi_loose_volume",
        display_name="이동평균+RSI 거래량완화 (1.2배)",
        description="거래량 급증 기준을 1.5배→1.2배로 낮춰 진입 빈도/승률 트레이드오프 확인.",
        factory=lambda: MovingAverageRsiStrategy(
            MovingAverageRsiParams(volume_surge_ratio=1.2), name="ma_rsi_loose_volume"
        ),
        category=CATEGORY_HYBRID,
    ),
    # ── 추세추종 ──
    StrategyDefinition(
        key="golden_cross_20_60",
        display_name="골든크로스 (20/60)",
        description="단기 이동평균선이 장기선을 상향돌파하면 매수, 하향이탈하면 매도. 가장 고전적인 추세추종.",
        factory=lambda: GoldenCrossStrategy(GoldenCrossParams(20, 60), name="golden_cross_20_60"),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="golden_cross_5_20",
        display_name="골든크로스 단타형 (5/20)",
        description="같은 규칙을 5/20으로 좁힌 단기 버전. 신호가 훨씬 잦다.",
        factory=lambda: GoldenCrossStrategy(GoldenCrossParams(5, 20), name="golden_cross_5_20"),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="ema_cross_12_26",
        display_name="EMA 교차 (12/26)",
        description="지수이동평균 교차 — 최근 가격에 가중치를 줘 단순이동평균보다 빠르게 반응.",
        factory=lambda: EmaCrossStrategy(EmaCrossParams(12, 26), name="ema_cross_12_26"),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="macd_cross",
        display_name="MACD 신호선 교차 (12/26/9)",
        description="MACD선이 신호선을 상향돌파하면 매수, 하향이탈하면 매도. 가장 널리 쓰이는 추세 지표.",
        factory=lambda: MacdCrossStrategy(MacdCrossParams(), name="macd_cross"),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="macd_cross_positive",
        display_name="MACD 교차 + 0선 위 필터",
        description="MACD가 0보다 클 때(이미 상승 국면)의 교차만 매수 — 하락장 중 반짝 반등을 걸러낸다.",
        factory=lambda: MacdCrossStrategy(
            MacdCrossParams(require_positive_macd=True), name="macd_cross_positive"
        ),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="donchian_20_10",
        display_name="돈치안 돌파 (20일 진입/10일 청산)",
        description="20일 신고가 돌파 매수, 10일 신저가 이탈 매도. 이른바 터틀 트레이딩 규칙.",
        factory=lambda: DonchianBreakoutStrategy(
            DonchianBreakoutParams(20, 10), name="donchian_20_10"
        ),
        category=CATEGORY_TREND,
    ),
    StrategyDefinition(
        key="donchian_adx_filter",
        display_name="돈치안 돌파 + 추세강도(ADX) 필터",
        description="ADX 25 이상(추세장)일 때만 돌파 매수 — 횡보장의 가짜 돌파를 걸러낸다.",
        factory=lambda: DonchianBreakoutStrategy(
            DonchianBreakoutParams(20, 10, adx_filter=25), name="donchian_adx_filter"
        ),
        category=CATEGORY_TREND,
    ),
    # ── 평균회귀 ──
    StrategyDefinition(
        key="rsi_reversion",
        display_name="RSI 평균회귀 교과서형 (30/70 + 장기선 필터)",
        description=(
            "RSI 30 반등 매수 + 60일선 위에서만 진입. "
            "⚠️ 2023~2024 백테스트에서 거래 0건 — RSI가 30까지 빠질 만큼 하락하면 "
            "이미 60일선 아래인 경우가 대부분이라 두 조건이 사실상 공존하지 않는다. "
            "교과서 조합이 실전에서 왜 안 되는지를 보여주는 대조군으로 남겨 둔다."
        ),
        factory=lambda: RsiReversionStrategy(RsiReversionParams(), name="rsi_reversion"),
        category=CATEGORY_REVERSION,
    ),
    StrategyDefinition(
        key="rsi2_pullback",
        display_name="RSI(2) 눌림목 매수 (10/70 + 장기선 필터)",
        description=(
            "RSI 기간을 2일로 짧게 잡아 '상승추세 중 얕은 눌림'을 잡는다. "
            "RSI(14)로는 장기선 필터와 공존이 불가능했던 문제를 실제로 해결한 버전 "
            "(종목당 5~13회 진입 확인)."
        ),
        factory=lambda: RsiReversionStrategy(
            RsiReversionParams(rsi_period=2, oversold=10, overbought=70), name="rsi2_pullback"
        ),
        category=CATEGORY_REVERSION,
    ),
    StrategyDefinition(
        key="rsi_reversion_aggressive",
        display_name="RSI 평균회귀 공격형 (35/65, 필터 없음)",
        description="기준을 완화하고 장기 이동평균 필터도 뺀 버전 — 진입은 늘지만 하락장에서 물릴 위험이 커진다.",
        factory=lambda: RsiReversionStrategy(
            RsiReversionParams(oversold=35, overbought=65, require_above_long_ma=False),
            name="rsi_reversion_aggressive",
        ),
        category=CATEGORY_REVERSION,
    ),
    StrategyDefinition(
        key="bollinger_reversion",
        display_name="볼린저 하단 반등 (20/2σ)",
        description="하단 밴드를 벗어났다 복귀하면 매수, 중심선 도달하면 청산. 박스권에서 잘 통하는 전형적 평균회귀.",
        factory=lambda: BollingerReversionStrategy(
            BollingerReversionParams(), name="bollinger_reversion"
        ),
        category=CATEGORY_REVERSION,
    ),
    StrategyDefinition(
        key="bollinger_reversion_wide",
        display_name="볼린저 하단 반등 넓은밴드 (20/2.5σ)",
        description="밴드를 2.5σ로 넓혀 더 극단적으로 빠졌을 때만 진입 — 빈도는 줄고 한 건당 기대값은 커진다.",
        factory=lambda: BollingerReversionStrategy(
            BollingerReversionParams(num_std=2.5, exit_at_middle=False),
            name="bollinger_reversion_wide",
        ),
        category=CATEGORY_REVERSION,
    ),
    StrategyDefinition(
        key="stochastic_20_80",
        display_name="스토캐스틱 교차 (14/3, 20·80)",
        description="과매도 구간에서 %K가 %D 상향돌파 시 매수, 과매수 구간 하향이탈 시 매도.",
        factory=lambda: StochasticStrategy(StochasticParams(), name="stochastic_20_80"),
        category=CATEGORY_REVERSION,
    ),
    # ── 돌파·모멘텀 ──
    StrategyDefinition(
        key="bollinger_breakout",
        display_name="볼린저 상단 돌파 (거래량 확인)",
        description="상단 밴드를 거래량 급증과 함께 뚫으면 매수. 같은 지표를 평균회귀와 정반대로 해석한 가설.",
        factory=lambda: BollingerBreakoutStrategy(
            BollingerBreakoutParams(), name="bollinger_breakout"
        ),
        category=CATEGORY_BREAKOUT,
    ),
    StrategyDefinition(
        key="volume_surge_5d",
        display_name="거래량 급증 단타 (2배, 5일 보유)",
        description="거래량 2배 급증 + 2% 이상 상승 시 매수, 5거래일 뒤 무조건 청산. 시간 기준 청산이 특징.",
        factory=lambda: VolumeSurgeStrategy(VolumeSurgeParams(), name="volume_surge_5d"),
        category=CATEGORY_BREAKOUT,
    ),
    StrategyDefinition(
        key="volume_surge_3d",
        display_name="거래량 급증 초단타 (3배, 3일 보유)",
        description="더 강한 급증(3배)만 잡고 3일 만에 청산 — 재료 소멸 전에 빠지는 걸 노린 가설.",
        factory=lambda: VolumeSurgeStrategy(
            VolumeSurgeParams(volume_surge_ratio=3.0, holding_days=3), name="volume_surge_3d"
        ),
        category=CATEGORY_BREAKOUT,
    ),
    StrategyDefinition(
        key="price_channel_20",
        display_name="종가 신고가 돌파 (20일)",
        description="20일 종가 신고가를 넘으면 매수, 20일선 이탈 시 매도. 장중 흔들림에 덜 반응하는 돌파.",
        factory=lambda: PriceChannelBreakoutStrategy(
            PriceChannelParams(), name="price_channel_20"
        ),
        category=CATEGORY_BREAKOUT,
    ),
    StrategyDefinition(
        key="price_channel_60_strict",
        display_name="종가 신고가 돌파 장기·엄격 (60일, +1%)",
        description="60일 신고가를 1% 이상 확실히 뚫어야 진입 — 가짜 돌파를 최대한 걸러낸 버전.",
        factory=lambda: PriceChannelBreakoutStrategy(
            PriceChannelParams(lookback=60, breakout_pct=1.0, exit_sma=20),
            name="price_channel_60_strict",
        ),
        category=CATEGORY_BREAKOUT,
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


def list_definitions(category: str | None = None) -> list[StrategyDefinition]:
    if category is None:
        return list(REGISTRY)
    return [d for d in REGISTRY if d.category == category]
