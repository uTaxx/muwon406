from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from muwon.domain.types import OrderResult, OrderSide, Signal


class MarketDataSource(ABC):
    """일봉 OHLCV 등 시세 데이터를 제공하는 소스의 공통 인터페이스."""

    @abstractmethod
    def get_daily_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        """columns: [trade_date, open, high, low, close, volume]"""
        raise NotImplementedError


class Strategy(ABC):
    """가격 히스토리를 입력받아 매매 신호를 생성하는 전략의 공통 인터페이스.

    규칙기반 전략과 ML 기반 전략이 동일한 인터페이스를 구현하므로,
    전략 엔진에서 서로 교체해 사용할 수 있다.
    """

    name: str

    @abstractmethod
    def generate_signals(self, price_history: pd.DataFrame) -> list[Signal]:
        raise NotImplementedError


class OrderExecutor(ABC):
    """모의투자/실전투자 주문 실행의 공통 인터페이스."""

    @abstractmethod
    def submit_order(self, symbol: str, side: OrderSide, quantity: int) -> OrderResult:
        raise NotImplementedError
