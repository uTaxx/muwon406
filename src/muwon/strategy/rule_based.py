"""이동평균+거래량 추세추종과 RSI 평균회귀를 결합한 1단계 규칙기반 전략.

매수 트리거 두 가지 (서로 독립적):
  - trend: 종가가 20일 이동평균을 상향 돌파 + 거래량이 20일 평균의 1.5배
    이상 + RSI14가 70 미만(과매수 아님)
  - reversion: RSI14가 30 밑에서 위로 반등 + 60일선 위(추세 자체는 살아있는
    구간)에서만 — 하락 추세 중 반짝 반등을 잡는 걸 피하기 위한 필터

매도 트리거:
  - 20일선 하향 이탈, 또는 RSI14가 80 초과(과매수 청산)

손절/포지션 크기 같은 자금관리는 이 전략이 아니라 RiskManager가 책임진다 —
여기서는 방향 신호만 낸다.
"""

import pandas as pd

from muwon.domain.interfaces import Strategy
from muwon.domain.types import Signal, SignalType
from muwon.indicators.technical import add_indicators

VOLUME_SURGE_RATIO = 1.5
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 80
RSI_BUY_CEILING = 70


class MovingAverageRsiStrategy(Strategy):
    name = "ma_rsi_v1"

    def generate_signals(self, symbol: str, price_history: pd.DataFrame) -> list[Signal]:
        df = add_indicators(price_history)
        signals: list[Signal] = []

        for i in range(1, len(df)):
            prev, cur = df.iloc[i - 1], df.iloc[i]
            if pd.isna(cur["sma20"]) or pd.isna(prev["sma20"]) or pd.isna(cur["rsi14"]):
                continue

            golden_cross = prev["close"] <= prev["sma20"] and cur["close"] > cur["sma20"]
            volume_surge = (
                not pd.isna(cur["volume_ma20"])
                and cur["volume_ma20"] > 0
                and cur["volume"] >= cur["volume_ma20"] * VOLUME_SURGE_RATIO
            )
            if golden_cross and volume_surge and cur["rsi14"] < RSI_BUY_CEILING:
                signals.append(
                    Signal(
                        symbol=symbol,
                        trade_date=cur["trade_date"],
                        signal_type=SignalType.BUY,
                        strategy_name=self.name,
                        reason="20일선 상향돌파 + 거래량 급증",
                    )
                )
                continue

            rsi_bounce = (
                not pd.isna(prev["rsi14"])
                and prev["rsi14"] < RSI_OVERSOLD <= cur["rsi14"]
                and not pd.isna(cur["sma60"])
                and cur["close"] > cur["sma60"]
            )
            if rsi_bounce:
                signals.append(
                    Signal(
                        symbol=symbol,
                        trade_date=cur["trade_date"],
                        signal_type=SignalType.BUY,
                        strategy_name=self.name,
                        reason="RSI 과매도 반등",
                    )
                )
                continue

            dead_cross = prev["close"] >= prev["sma20"] and cur["close"] < cur["sma20"]
            if dead_cross:
                signals.append(
                    Signal(
                        symbol=symbol,
                        trade_date=cur["trade_date"],
                        signal_type=SignalType.SELL,
                        strategy_name=self.name,
                        reason="20일선 하향이탈",
                    )
                )
                continue

            if cur["rsi14"] > RSI_OVERBOUGHT:
                signals.append(
                    Signal(
                        symbol=symbol,
                        trade_date=cur["trade_date"],
                        signal_type=SignalType.SELL,
                        strategy_name=self.name,
                        reason="RSI 과매수",
                    )
                )

        return signals
