from dataclasses import dataclass
from datetime import date
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True)
class PriceBar:
    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True)
class Signal:
    symbol: str
    trade_date: date
    signal_type: SignalType
    strategy_name: str
    score: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class FillInfo:
    """주문이 실제로 얼마에·몇 주나 체결됐는지.

    OrderResult.price는 주문을 넣을 때 우리가 갖고 있던 기준가(직전 종가)일
    뿐 실제 체결가가 아니다 — 시장가 주문은 넣어봐야 얼마에 되는지 알 수
    있어서, 기준가만 기록하면 손익 집계에 오차가 계속 쌓인다. 체결 조회로
    받아온 진짜 값을 담는 자리다.

    filled_quantity가 주문 수량보다 적을 수 있다(부분 체결). 0이면 아직
    체결되지 않았거나 거부된 것이다."""

    order_id: str
    symbol: str
    ordered_quantity: int
    filled_quantity: int
    avg_fill_price: float

    @property
    def is_fully_filled(self) -> bool:
        return self.filled_quantity >= self.ordered_quantity > 0

    @property
    def is_unfilled(self) -> bool:
        return self.filled_quantity == 0


@dataclass(frozen=True)
class OrderResult:
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    order_id: str
    is_paper: bool
