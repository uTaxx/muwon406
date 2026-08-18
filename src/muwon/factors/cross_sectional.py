"""전 종목을 한꺼번에 봐야 계산되는 Factor — 상대강도와 시장 국면.

이 둘은 예전 인터페이스에서는 **만들 수가 없었다.** generate_signals(symbol, df)
에는 다른 종목도 지수도 들어오지 않기 때문이다. Phase 1에서 판단 단위를
'종목'에서 '하루'로 올린 이유가 정확히 이것이다.
"""

from __future__ import annotations

from muwon.factors.base import Factor, history_up_to, pct_return, percentile_scores
from muwon.strategy.portfolio import FactorResult, MarketContext


class RelativeStrengthFactor(Factor):
    """남들보다 잘하고 있는가 — 유니버스 안에서의 수익률 순위.

    절대 수익률(Momentum)과 다르다. 시장 전체가 20% 오른 구간에서 10% 오른
    종목은 절대로는 좋아 보여도 상대로는 하위권이다. 추세추종에서 오래
    검증된 변수라 인수인계서도 9항에서 따로 떼어 놓았다.

    기준지수를 넘겨받으면 초과수익(종목-지수)으로, 없으면 종목 수익률 자체로
    순위를 매긴다. 지수 조회가 막혀도 Factor가 통째로 죽지 않게 하려는 것이다."""

    key = "relative_strength"

    def prepare(self, ctx: MarketContext) -> None:
        period = int(self.params.get("period", 60))
        index_return = None
        if ctx.index_history is not None and len(ctx.index_history):
            idx = ctx.index_history[ctx.index_history["trade_date"] <= ctx.as_of]
            if len(idx):
                index_return = pct_return(idx["close"], period)

        self._raw: dict[str, float] = {}
        for symbol in ctx.histories:
            df = history_up_to(ctx, symbol)
            if df is None:
                continue
            r = pct_return(df["close"], period)
            if r is None:
                continue
            self._raw[symbol] = r - index_return if index_return is not None else r

        self._ranked = percentile_scores(self._raw)
        self._period = period
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

    def prepare(self, ctx: MarketContext) -> None:
        short_ma = int(self.params.get("short_ma", 20))
        long_ma = int(self.params.get("long_ma", 60))

        above_short = above_long = counted = 0
        for symbol in ctx.histories:
            df = history_up_to(ctx, symbol)
            if df is None or len(df) < long_ma + 1:
                continue
            closes = df["close"]
            price = float(closes.iloc[-1])
            counted += 1
            if price > float(closes.rolling(short_ma).mean().iloc[-1]):
                above_short += 1
            if price > float(closes.rolling(long_ma).mean().iloc[-1]):
                above_long += 1

        if counted == 0:
            self.regime: str | None = None
            self.breadth_short = self.breadth_long = 0.0
            return

        self.breadth_short = above_short / counted * 100
        self.breadth_long = above_long / counted * 100
        self.regime = self._classify(self.breadth_short, self.breadth_long)
        self._counted = counted

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
