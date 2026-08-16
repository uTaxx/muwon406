"""TradingEngine(일 1회)과 RealtimeTradingEngine(장중 상시)이 공유하는
포지션/주문/가상현금 저장소.

두 엔진이 같은 DB 상태를 쓰는 건, 이 함수들이 둘 다 재사용되기 때문이지
두 엔진을 동시에 같은 계좌에 돌리라는 뜻이 아니다 — 배치(GitHub Actions)와
장중 상시(VPS)는 서로 다른 운영 모드로, 한 번에 하나만 실제 계좌에 붙여
쓸 것을 전제로 한다."""

from __future__ import annotations

from muwon.db.models import EngineStateRow, OrderRow, PositionRow
from muwon.domain.types import OrderResult


def load_positions(session_factory) -> dict[str, PositionRow]:
    with session_factory() as session:
        rows = session.query(PositionRow).all()
        session.expunge_all()
        return {row.symbol: row for row in rows}


def save_position(session_factory, position: PositionRow) -> None:
    with session_factory() as session:
        session.merge(position)
        session.commit()


def delete_position(session_factory, symbol: str) -> None:
    with session_factory() as session:
        row = session.get(PositionRow, symbol)
        if row is not None:
            session.delete(row)
            session.commit()


def record_order(session_factory, order: OrderResult, reason: str) -> None:
    with session_factory() as session:
        session.add(
            OrderRow(
                symbol=order.symbol,
                side=order.side.value,
                quantity=order.quantity,
                price=order.price,
                is_paper=order.is_paper,
                kis_order_id=order.order_id,
                reason=reason,
            )
        )
        session.commit()


def load_engine_state(session_factory, initial_cash: float) -> tuple[float, float]:
    """(cash, day_start_equity)를 돌려준다. day_start_equity는 '직전 실행이
    끝난 시점의 평가금액' 기준점 — 상태가 아예 없는 첫 실행이면 남아 있는
    포지션을 진입가로 어림잡아 기준을 만든다."""
    with session_factory() as session:
        cash_row = session.get(EngineStateRow, "cash")
        equity_row = session.get(EngineStateRow, "day_start_equity")

        cash = float(cash_row.value) if cash_row else initial_cash
        if equity_row is not None:
            day_start_equity = float(equity_row.value)
        else:
            positions_value = sum(p.quantity * p.entry_price for p in session.query(PositionRow).all())
            day_start_equity = cash + positions_value
        return cash, day_start_equity


def save_engine_state(session_factory, cash: float, day_start_equity: float) -> None:
    with session_factory() as session:
        for key, value in (("cash", str(cash)), ("day_start_equity", str(day_start_equity))):
            row = session.get(EngineStateRow, key)
            if row is None:
                session.add(EngineStateRow(key=key, value=value))
            else:
                row.value = value
        session.commit()
