"""KIS 서버로 실제(또는 KIS 모의투자) 주문을 넣는 OrderExecutor 구현체.

TradingEngine은 OrderExecutor 인터페이스만 알기 때문에, 개발 중에는
SimulatedOrderExecutor를, KIS 네트워크 접근이 되는 환경에서는 이걸로
바꿔 끼우기만 하면 된다."""

from __future__ import annotations

from muwon.data.kis_client import KISClient
from muwon.domain.interfaces import OrderExecutor
from muwon.domain.types import OrderResult, OrderSide


class KISOrderExecutor(OrderExecutor):
    def __init__(self, client: KISClient):
        self._client = client

    def submit_order(
        self, symbol: str, side: OrderSide, quantity: int, reference_price: float
    ) -> OrderResult:
        return self._client.place_cash_order(symbol, side, quantity, reference_price)
