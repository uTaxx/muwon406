"""종목 하나만 보고 계산하는 Factor들 — Trend / Momentum / Pullback / Volume.

이 넷은 예전 구조에서도 만들 수 있었던 것들이다. 달라진 건 참/거짓이 아니라
0~100 점수를 돌려준다는 점, 그리고 왜 그 점수인지 문장을 함께 남긴다는 점이다.
"""

from __future__ import annotations

from itertools import pairwise
from typing import ClassVar

import pandas as pd

from muwon.factors.base import (
    Factor,
    history_up_to,
    pct_return,
    percentile_scores,
    piecewise,
    ratio_score,
)
from muwon.strategy.portfolio import FactorResult, MarketContext


class TrendFactor(Factor):
    """정배열이 얼마나 완성됐는가.

    '20일선 위에 있다'를 참/거짓으로 보면 40일선 위에 겨우 걸친 종목과
    모든 선 위에서 완만히 오르는 종목이 같은 취급을 받는다. 사다리를 여러
    칸으로 나눠 몇 칸을 올라섰는지로 본다."""

    key = "trend"

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        df = history_up_to(ctx, symbol)
        windows = self.params.get("mas", [20, 60, 120])
        if df is None or len(df) < max(windows) + 1:
            return FactorResult(self.key, None, "데이터 부족")

        close = df["close"]
        mas = {w: float(close.rolling(w).mean().iloc[-1]) for w in windows}
        price = float(close.iloc[-1])

        checks: list[tuple[bool, str]] = [(price > mas[w], f"종가>{w}일선") for w in windows]
        # 선끼리의 순서(정배열)도 본다 — 가격만 보면 급등 하루로 만점이 나온다
        for short, long in pairwise(windows):
            checks.append((mas[short] > mas[long], f"{short}>{long}일선"))

        passed = [label for ok, label in checks if ok]
        score = ratio_score(len(passed), len(checks))
        detail = ", ".join(passed) if passed else "역배열"
        return FactorResult(self.key, score, f"정배열 {len(passed)}/{len(checks)} ({detail})")


class MomentumFactor(Factor):
    """이 종목 자체가 오르고 있는가 — 여러 기간을 섞어 본다.

    최근 수익률만 보면 하루 급등에 속는다. 인수인계서 8.2항대로 장기
    모멘텀에 더 큰 비중을 둔다. 절대 수익률을 점수로 바꿀 때 임계값을 손으로
    정하면 시장 국면에 따라 전 종목이 0점이나 100점이 되므로, 혼합 수익률을
    유니버스 안에서의 백분위로 바꾼다."""

    key = "momentum"
    DEFAULT_WEIGHTS: ClassVar[dict[int, float]] = {5: 0.15, 20: 0.20, 60: 0.30, 120: 0.35}

    def prepare(self, ctx: MarketContext) -> None:
        weights: dict[int, float] = {
            int(k): float(v) for k, v in (self.params.get("weights") or self.DEFAULT_WEIGHTS).items()
        }
        self._blend: dict[str, float] = {}
        self._detail: dict[str, str] = {}
        for symbol in ctx.histories:
            df = history_up_to(ctx, symbol)
            if df is None:
                continue
            closes = df["close"]
            parts, used_weight, labels = 0.0, 0.0, []
            for period, weight in weights.items():
                r = pct_return(closes, period)
                if r is None:
                    continue
                parts += r * weight
                used_weight += weight
                labels.append(f"{period}일 {r:+.1f}%")
            if used_weight <= 0:
                continue
            # 계산된 기간의 가중치만으로 다시 나눠, 데이터가 짧은 종목이
            # 무조건 낮은 값을 받지 않게 한다
            self._blend[symbol] = parts / used_weight
            self._detail[symbol] = ", ".join(labels)
        self._ranked = percentile_scores(self._blend)

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        if symbol not in self._ranked:
            return FactorResult(self.key, None, "데이터 부족")
        return FactorResult(
            self.key,
            self._ranked[symbol],
            f"모멘텀 {self._blend[symbol]:+.1f}% ({self._detail[symbol]})",
        )


class PullbackFactor(Factor):
    """상승 추세 중의 눌림인가.

    많이 떨어졌다고 좋은 게 아니다(인수인계서 10항). 추세가 살아 있는 상태의
    -4~-6% 조정이 가장 높고, 그보다 얕으면 기회가 아니며, 너무 깊으면 추세
    훼손으로 본다. 장기선 아래로 내려간 종목은 아예 눌림으로 치지 않는다."""

    key = "pullback"
    #: (조정폭 %, 점수) — 오름차순
    DEFAULT_CURVE: ClassVar[list[tuple[float, float]]] = [(-12.0, 10.0), (-8.0, 70.0), (-6.0, 100.0), (-4.0, 70.0), (-2.0, 30.0), (0.0, 10.0)]

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        df = history_up_to(ctx, symbol)
        lookback = int(self.params.get("lookback", 5))
        trend_ma = int(self.params.get("trend_ma", 60))
        if df is None or len(df) < trend_ma + 1:
            return FactorResult(self.key, None, "데이터 부족")

        closes = df["close"]
        price = float(closes.iloc[-1])
        long_ma = float(closes.rolling(trend_ma).mean().iloc[-1])
        if price <= long_ma:
            return FactorResult(self.key, 0.0, f"{trend_ma}일선 아래 — 눌림이 아니라 하락")

        recent_high = float(closes.iloc[-(lookback + 1) :].max())
        if recent_high <= 0:
            return FactorResult(self.key, None, "데이터 부족")
        dip_pct = (price / recent_high - 1) * 100

        curve = [(float(x), float(y)) for x, y in (self.params.get("curve") or self.DEFAULT_CURVE)]
        return FactorResult(
            self.key,
            piecewise(dip_pct, curve),
            f"최근 {lookback}일 고점 대비 {dip_pct:+.1f}% (추세 유지)",
        )


class VolumeFactor(Factor):
    """관심이 몰렸는가 — 평균 거래량 대비 배수.

    유동성 하한도 여기서 본다. 거래대금이 너무 작은 종목은 신호가 맞아도
    실제로는 원하는 가격에 못 산다(인수인계서 12항)."""

    key = "volume"
    DEFAULT_CURVE: ClassVar[list[tuple[float, float]]] = [(0.5, 0.0), (1.0, 30.0), (1.5, 60.0), (2.0, 80.0), (3.0, 100.0)]

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        df = history_up_to(ctx, symbol)
        window = int(self.params.get("ma_window", 20))
        if df is None or len(df) < window + 1:
            return FactorResult(self.key, None, "데이터 부족")

        volume_ma = float(df["volume"].rolling(window).mean().iloc[-1])
        if volume_ma <= 0:
            return FactorResult(self.key, None, "거래량 데이터 없음")

        min_turnover = float(self.params.get("min_turnover_krw", 0))
        if min_turnover > 0:
            turnover = volume_ma * float(df["close"].iloc[-1])
            if turnover < min_turnover:
                return FactorResult(
                    self.key, 0.0, f"유동성 미달 (평균 거래대금 {turnover / 1e8:.1f}억)"
                )

        ratio = float(df["volume"].iloc[-1]) / volume_ma
        curve = [(float(x), float(y)) for x, y in (self.params.get("curve") or self.DEFAULT_CURVE)]
        return FactorResult(self.key, piecewise(ratio, curve), f"거래량 평균 대비 {ratio:.1f}배")


def _latest_close(df: pd.DataFrame) -> float:
    return float(df["close"].iloc[-1])
