"""전 종목을 한꺼번에 봐야 계산되는 Factor — 상대강도와 시장 국면.

이 둘은 예전 인터페이스에서는 **만들 수가 없었다.** generate_signals(symbol, df)
에는 다른 종목도 지수도 들어오지 않기 때문이다. Phase 1에서 판단 단위를
'종목'에서 '하루'로 올린 이유가 정확히 이것이다.

계산은 두 단계로 나뉜다. warmup()은 종목별 시계열을 한 번만 만들고,
prepare()는 날짜마다 그 표에서 그날 값을 꺼내 횡단면(순위·비율)을 구한다.
"""

from __future__ import annotations

import pandas as pd

from muwon.factors.base import Factor, percentile_scores
from muwon.strategy.portfolio import FactorResult, MarketContext


def _closes(df: pd.DataFrame) -> pd.Series:
    return df.set_index("trade_date")["close"]


class RelativeStrengthFactor(Factor):
    """남들보다 잘하고 있는가 — 유니버스 안에서의 수익률 순위.

    절대 수익률(Momentum)과 다르다. 시장 전체가 20% 오른 구간에서 10% 오른
    종목은 절대로는 좋아 보여도 상대로는 하위권이다. 추세추종에서 오래
    검증된 변수라 인수인계서도 9항에서 따로 떼어 놓았다.

    기준지수를 넘겨받으면 초과수익(종목-지수)으로, 없으면 종목 수익률 자체로
    순위를 매긴다. 지수 조회가 막혀도 Factor가 통째로 죽지 않게 하려는 것이다."""

    key = "relative_strength"

    def warmup(self, histories: dict[str, pd.DataFrame]) -> None:
        self._period = int(self.params.get("period", 60))
        self._returns: dict[str, pd.Series] = {}
        for symbol, df in histories.items():
            if len(df) == 0:
                continue
            closes = _closes(df)
            self._returns[symbol] = (closes / closes.shift(self._period) - 1) * 100
        self._index_returns: pd.Series | None = None

    def prepare(self, ctx: MarketContext) -> None:
        if self._index_returns is None and ctx.index_history is not None and len(ctx.index_history):
            closes = _closes(ctx.index_history)
            self._index_returns = (closes / closes.shift(self._period) - 1) * 100

        index_return = None
        if self._index_returns is not None and ctx.as_of in self._index_returns.index:
            value = self._index_returns.loc[ctx.as_of]
            if pd.notna(value):
                index_return = float(value)

        self._raw = {}
        for symbol, series in self._returns.items():
            if ctx.as_of not in series.index:
                continue
            value = series.loc[ctx.as_of]
            if pd.isna(value):
                continue
            self._raw[symbol] = float(value) - index_return if index_return is not None else float(value)

        self._ranked = percentile_scores(self._raw)
        self._vs_index = index_return is not None

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        if symbol not in self._ranked:
            return FactorResult(self.key, None, "데이터 부족")
        basis = "지수 대비" if self._vs_index else "유니버스 내"
        return FactorResult(
            self.key,
            self._ranked[symbol],
            f"{self._period}일 상대강도 상위 {100 - self._ranked[symbol]:.0f}% "
            f"({basis} {self._raw[symbol]:+.1f}%)",
        )


#: Breadth(20일선 위 종목 비율)로 국면을 나눈다. 지수 데이터 없이도 판정할 수
#: 있어야 해서 우리 유니버스 자체를 시장의 대리 지표로 쓴다 — 시총 상위
#: 60종목이면 시장 방향을 읽는 표본으로는 충분하다.
REGIME_SCORES = {"STRONG_BULL": 100.0, "BULL": 75.0, "NEUTRAL": 50.0, "BEAR": 20.0}


class MarketRegimeFactor(Factor):
    """시장 자체가 살 만한 환경인가 — 개별 종목보다 상위 판단.

    아무리 좋은 종목도 시장이 무너지는 구간에서는 같이 빠진다. 그래서 이
    Factor는 점수에 들어갈 뿐 아니라, 국면에 따라 매수 기준선 자체를 올린다
    (약세장에서는 웬만한 점수로는 못 사게 한다)."""

    key = "market_regime"

    def warmup(self, histories: dict[str, pd.DataFrame]) -> None:
        short_ma = int(self.params.get("short_ma", 20))
        long_ma = int(self.params.get("long_ma", 60))
        self._above: dict[str, pd.DataFrame] = {}
        for symbol, df in histories.items():
            if len(df) == 0:
                continue
            closes = _closes(df)
            short = closes.rolling(short_ma).mean()
            long = closes.rolling(long_ma).mean()
            # 이동평균이 아직 안 만들어진 구간은 NaN으로 남겨 '집계 대상 아님'이
            # 되게 한다. 0으로 채우면 상장 초기 종목이 전부 '선 아래'로 잡혀
            # Breadth가 실제보다 낮게 나온다.
            self._above[symbol] = pd.DataFrame(
                {"short": (closes > short).where(long.notna()), "long": (closes > long).where(long.notna())}
            )
        self.regime: str | None = None
        self.breadth_short = self.breadth_long = 0.0

    def prepare(self, ctx: MarketContext) -> None:
        short_hits = long_hits = counted = 0
        for table in self._above.values():
            if ctx.as_of not in table.index:
                continue
            row = table.loc[ctx.as_of]
            if pd.isna(row["long"]):
                continue
            counted += 1
            short_hits += int(bool(row["short"]))
            long_hits += int(bool(row["long"]))

        if counted == 0:
            self.regime = None
            self.breadth_short = self.breadth_long = 0.0
            return

        self.breadth_short = short_hits / counted * 100
        self.breadth_long = long_hits / counted * 100
        self.regime = self._classify(self.breadth_short, self.breadth_long)

    def _classify(self, short_pct: float, long_pct: float) -> str:
        strong = float(self.params.get("strong_bull_breadth", 65))
        bull = float(self.params.get("bull_breadth", 50))
        bear = float(self.params.get("bear_breadth", 40))
        if short_pct >= strong and long_pct >= strong:
            return "STRONG_BULL"
        if short_pct >= bull and long_pct >= bull:
            return "BULL"
        if long_pct < bear:
            return "BEAR"
        return "NEUTRAL"

    def score(self, symbol: str, ctx: MarketContext) -> FactorResult:
        """국면 점수는 전 종목에 같은 값이 들어간다.

        종목을 고르는 데는 기여하지 않지만(다 같은 점수라 순위가 안 바뀐다),
        총점을 끌어내려 '약세장에서는 아무것도 안 사게' 만드는 역할을 한다."""
        if self.regime is None:
            return FactorResult(self.key, None, "국면 판정 불가")
        return FactorResult(
            self.key,
            REGIME_SCORES[self.regime],
            f"{self.regime} (20일선 위 {self.breadth_short:.0f}%, "
            f"60일선 위 {self.breadth_long:.0f}%)",
        )
