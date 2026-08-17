"""가격 데이터프레임에 전략이 참조하는 기술적 지표를 추가한다."""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator


def add_indicators(
    price_history: pd.DataFrame,
    sma_short: int = 20,
    sma_long: int = 60,
    rsi_period: int = 14,
    volume_ma_window: int = 20,
) -> pd.DataFrame:
    """price_history: [trade_date, open, high, low, close, volume].
    반환값에 sma_short, sma_long, rsi, volume_ma 컬럼이 추가된다(윈도우
    값 그대로가 컬럼명에 들어가진 않는다 — 호출부는 컬럼명이 아니라 이
    고정된 4개 이름으로 접근한다). 윈도우를 파라미터화한 이유는 같은 전략
    로직이라도 윈도우만 다른 여러 가설(예: 단타용 5/20 vs 스윙용 20/60)을
    같은 코드로 비교할 수 있게 하기 위해서다. 초반 구간(윈도우 미충족)은
    NaN이므로 사용하는 쪽에서 걸러야 한다."""
    df = price_history.sort_values("trade_date").reset_index(drop=True)
    df["sma_short"] = SMAIndicator(df["close"], window=sma_short).sma_indicator()
    df["sma_long"] = SMAIndicator(df["close"], window=sma_long).sma_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=rsi_period).rsi()
    df["volume_ma"] = df["volume"].rolling(window=volume_ma_window).mean()
    return df
