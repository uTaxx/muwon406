"""여러 전략이 공유하는 작은 도우미들.

전략마다 "직전 봉과 현재 봉을 비교해 교차를 판정한다"거나 "Signal을
만든다"는 코드가 똑같이 반복되므로 여기 모았다."""

from __future__ import annotations

import pandas as pd

from muwon.domain.types import Signal, SignalType


def crossed_above(prev_value: float, cur_value: float, prev_ref: float, cur_ref: float) -> bool:
    """직전엔 기준선 이하였는데 지금은 위로 올라섰는가 (상향 돌파)."""
    if pd.isna(prev_value) or pd.isna(cur_value) or pd.isna(prev_ref) or pd.isna(cur_ref):
        return False
    return prev_value <= prev_ref and cur_value > cur_ref


def crossed_below(prev_value: float, cur_value: float, prev_ref: float, cur_ref: float) -> bool:
    """직전엔 기준선 이상이었는데 지금은 아래로 내려섰는가 (하향 이탈)."""
    if pd.isna(prev_value) or pd.isna(cur_value) or pd.isna(prev_ref) or pd.isna(cur_ref):
        return False
    return prev_value >= prev_ref and cur_value < cur_ref


def make_signal(
    symbol: str, row: pd.Series, signal_type: SignalType, strategy_name: str, reason: str
) -> Signal:
    return Signal(
        symbol=symbol,
        trade_date=row["trade_date"],
        signal_type=signal_type,
        strategy_name=strategy_name,
        reason=reason,
    )


def has_nan(row: pd.Series, columns: list[str]) -> bool:
    """지표 계산 초반 구간(윈도우 미충족)은 NaN이라 판정에서 제외해야 한다."""
    return any(pd.isna(row[c]) for c in columns)
