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
    def generate_signals(self, symbol: str, price_history: pd.DataFrame) -> list[Signal]:
        """price_history: [trade_date, open, high, low, close, volume] 컬럼을 가진,
        날짜 오름차순으로 정렬된 단일 종목의 가격 히스토리."""
        raise NotImplementedError


class OrderExecutor(ABC):
    """모의투자/실전투자 주문 실행의 공통 인터페이스.

    reference_price는 시장가 주문의 체결가를 미리 알 수 없다는 전제로,
    엔진이 이미 갖고 있는 최신 종가를 기록·수량계산용 기준가로 넘기는
    값이다. 실제 체결가 조회(주문 조회 API)는 이 MVP 범위 밖이다."""

    @abstractmethod
    def submit_order(
        self, symbol: str, side: OrderSide, quantity: int, reference_price: float
    ) -> OrderResult:
        raise NotImplementedError
