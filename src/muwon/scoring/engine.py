"""Factor 점수를 합쳐 매수/매도를 판단하는 엔진.

이 파일은 개별 Factor가 무엇을 하는지 전혀 모른다. 목록을 받아 순회하고,
가중치를 적용하고, 임계값과 비교할 뿐이다. Factor를 새로 추가할 때 이 파일을
고칠 일이 없어야 한다는 게 설계 목표다(인수인계서 33항).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from muwon.domain.types import Signal, SignalType
from muwon.factors.base import Factor
from muwon.factors.cross_sectional import MarketRegimeFactor, RelativeStrengthFactor
from muwon.factors.technical import (
    MomentumFactor,
    PullbackFactor,
    TrendFactor,
    VolumeFactor,
)
from muwon.scoring.config import StrategyConfig
from muwon.strategy.portfolio import MarketContext, PortfolioStrategy

#: key → Factor 클래스. 새 Factor는 여기 한 줄만 추가한다.
FACTOR_REGISTRY: dict[str, type[Factor]] = {
    "trend": TrendFactor,
    "momentum": MomentumFactor,
    "pullback": PullbackFactor,
    "volume": VolumeFactor,
    "relative_strength": RelativeStrengthFactor,
    "market_regime": MarketRegimeFactor,
}


@dataclass(frozen=True)
class ScoredSymbol:
    """한 종목의 최종 평가 — 점수와 근거가 항상 함께 다닌다."""

    symbol: str
    total: float
    decision: str  # NO_TRADE / WATCH / BUY / STRONG_BUY
    factor_scores: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def build_factors(config: StrategyConfig) -> list[Factor]:
    """설정에서 켜져 있고 구현이 있는 Factor만 만든다.

    설정에 있지만 아직 구현이 없는 key(fundamental, flow)는 조용히 건너뛴다 —
    자리를 미리 잡아 둔 것이라 없다고 터지면 안 된다."""
    factors = []
    for key, cfg in config.factors.items():
        if not cfg.enabled or cfg.weight <= 0:
            continue
        factor_cls = FACTOR_REGISTRY.get(key)
        if factor_cls is None:
            continue
        factors.append(factor_cls(cfg.params))
    return factors


class ScoreEngine:
    def __init__(self, config: StrategyConfig, factors: list[Factor] | None = None):
        self.config = config
        self.factors = factors if factors is not None else build_factors(config)
        self._warmed = False

    def warmup(self, histories) -> None:
        for factor in self.factors:
            factor.warmup(histories)
        self._warmed = True

    def evaluate(self, ctx: MarketContext) -> list[ScoredSymbol]:
        # 엔진이 prepare()를 안 불러 준 경우에도 동작해야 한다 — 테스트나
        # 단발 조회에서 warmup 없이 곧장 평가하는 경우가 있다.
        if not self._warmed:
            self.warmup(ctx.histories)
        for factor in self.factors:
            factor.prepare(ctx)

        regime = self._current_regime()
        buy_threshold = self.config.threshold_for(regime)
        strong = self.config.strong_buy_threshold

        results: list[ScoredSymbol] = []
        for symbol in ctx.histories:
            scores: dict[str, float] = {}
            reasons: list[str] = []
            skipped: list[str] = []

            for factor in self.factors:
                result = factor.score(symbol, ctx)
                if result.score is None:
                    skipped.append(f"{factor.key}: {result.reason}")
                    continue
                scores[factor.key] = result.score
                reasons.append(f"{factor.key} {result.score:.0f} — {result.reason}")

            # 평가된 Factor의 가중치만으로 100을 다시 채운다. 이게 없으면
            # Factor 하나를 끄거나 데이터가 하루 빠질 때마다 전 종목 총점이
            # 내려앉아 기준선(75점)의 의미가 달라진다.
            weights = self.config.enabled_weights(available=set(scores))
            if not weights:
                continue
            total = sum(scores[key] * weight / 100 for key, weight in weights.items())

            if total >= strong:
                decision = "STRONG_BUY"
            elif total >= buy_threshold:
                decision = "BUY"
            elif total >= buy_threshold - 10:
                decision = "WATCH"
            else:
                decision = "NO_TRADE"

            results.append(
                ScoredSymbol(symbol, total, decision, scores, reasons, skipped)
            )

        results.sort(key=lambda r: r.total, reverse=True)
        return results

    def _current_regime(self) -> str | None:
        for factor in self.factors:
            if isinstance(factor, MarketRegimeFactor):
                return factor.regime
        return None


class FactorScoreStrategy(PortfolioStrategy):
    """점수 합산 방식을 기존 전략과 같은 자리에 꽂는 어댑터.

    registry에 전략 하나로 등록되므로 대시보드·전략 리뷰·다기간 검증·리포트가
    전부 그대로 동작한다. 기존 21전략과 나란히 비교되는 게 핵심이다 — 새 방식이
    정말 나은지는 그 비교로만 알 수 있다."""

    def __init__(self, config: StrategyConfig | None = None, name: str = "factor_score_v1"):
        self.config = config or StrategyConfig()
        self.name = name
        self._engine = ScoreEngine(self.config)
        #: 마지막 평가 결과 — 판단 근거를 밖에서 꺼내 보기 위한 것
        self.last_results: list[ScoredSymbol] = []

    def prepare(self, histories) -> None:
        self._engine.warmup(histories)

    def evaluate(self, ctx: MarketContext) -> list[Signal]:
        self.last_results = self._engine.evaluate(ctx)
        signals: list[Signal] = []
        for result in self.last_results:
            if result.decision in ("BUY", "STRONG_BUY"):
                signals.append(
                    Signal(
                        symbol=result.symbol,
                        trade_date=ctx.as_of,
                        signal_type=SignalType.BUY,
                        strategy_name=self.name,
                        score=result.total,
                        reason=f"{result.decision} {result.total:.0f}점 — " + top_reason(result),
                    )
                )
            elif result.symbol in ctx.held and result.total < self.config.sell_threshold:
                # 점수 기반 청산 — 살 이유가 사라졌으면 들고 있을 이유도 없다
                signals.append(
                    Signal(
                        symbol=result.symbol,
                        trade_date=ctx.as_of,
                        signal_type=SignalType.SELL,
                        strategy_name=self.name,
                        score=result.total,
                        reason=f"점수 {result.total:.0f}점으로 하락 (기준 {self.config.sell_threshold:.0f})",
                    )
                )
        return signals


def top_reason(result: ScoredSymbol, limit: int = 2) -> str:
    """가장 크게 기여한 근거만 짧게 — 텔레그램 한 줄에 들어가야 한다."""
    ranked = sorted(result.factor_scores.items(), key=lambda kv: kv[1], reverse=True)
    return ", ".join(f"{key} {value:.0f}" for key, value in ranked[:limit])


def load_strategy_config() -> StrategyConfig:
    """DB에 저장된 설정을 읽되, 읽을 수 없으면 기본값으로 계속 간다.

    백테스트·테스트처럼 DB가 없는 자리에서도 전략을 만들 수 있어야 한다 —
    설정 저장소에 못 닿는다고 전략 생성이 실패하면 registry 전체가 죽는다."""
    try:
        from muwon.settings.service import build_settings_service

        return build_settings_service().get_strategy_config()
    except Exception:  # noqa: BLE001 — DB 부재·연결 실패 등 무엇이든 기본값으로
        return StrategyConfig()
