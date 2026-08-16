"""가격 데이터프레임에 전략이 참조하는 기술적 지표를 추가한다."""

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator


def add_indicators(price_history: pd.DataFrame) -> pd.DataFrame:
    """price_history: [trade_date, open, high, low, close, volume].
    반환값에 sma20, sma60, rsi14, volume_ma20 컬럼이 추가된다.
    초반 구간(윈도우 미충족)은 NaN이므로 사용하는 쪽에서 걸러야 한다."""
    df = price_history.sort_values("trade_date").reset_index(drop=True)
    df["sma20"] = SMAIndicator(df["close"], window=20).sma_indicator()
    df["sma60"] = SMAIndicator(df["close"], window=60).sma_indicator()
    df["rsi14"] = RSIIndicator(df["close"], window=14).rsi()
    df["volume_ma20"] = df["volume"].rolling(window=20).mean()
    return df
