"""실시간/모의투자용 신호→리스크→체결→알림→기록 1회 실행 엔진.

BacktestEngine과 최대한 같은 판단 로직(진입 조건, 손절, 비중 계산, 당일
손익 기준 서킷브레이커)을 쓰지만, 여긴 프로세스가 매번 새로 떠도 상태
(포지션·가상현금)가 이어져야 하므로 DB(positions/engine_state 테이블)에
둔다. run_once()는 하루에 한 번(장 마감 후, 그날 종가가 확정된 뒤) 호출하는
걸 전제로 설계했다 — 전략 자체가 일봉 기준이라 더 자주 돌릴 이유가 없다.

가상현금(engine_state.cash)은 KIS 실계좌 잔고를 조회하는 대신 이 엔진이
자체적으로 기록하는 값이다 — KIS 잔고조회 API 연동은 이 MVP 범위 밖이라,
KISOrderExecutor로 실제 주문을 넣더라도 리스크 계산(종목당 비중, 일일
손실한도)은 이 가상현금 기준으로 이뤄진다는 점에 주의할 것."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import sessionmaker

from muwon.backtest.costs import TransactionCosts
from muwon.data.universe import Ticker
from muwon.db.models import EngineStateRow, OrderRow, PositionRow
from muwon.domain.interfaces import MarketDataSource, OrderExecutor, Strategy
from muwon.domain.types import OrderSide, SignalType
from muwon.notify.telegram import TelegramNotifier
from muwon.risk.manager import RiskManager

HISTORY_LOOKBACK_DAYS = 120  # 60일선 등 지표 계산에 필요한 최소 여유


@dataclass
class ExecutedAction:
    symbol: str
    name: str
    side: OrderSide
    quantity: int
    price: float
    reason: str


@dataclass
class RunSummary:
    run_date: date | None
    checked_symbols: int
    actions: list[ExecutedAction] = field(default_factory=list)
    rejections: list[str] = field(default_factory=list)


class TradingEngine:
    def __init__(
        self,
        strategy: Strategy,
        risk_manager: RiskManager,
        data_source: MarketDataSource,
        order_executor: OrderExecutor,
        notifier: TelegramNotifier,
        session_factory: sessionmaker,
        universe: list[Ticker],
        source_symbol: Callable[[Ticker], str],
        costs: TransactionCosts | None = None,
        initial_cash: float = 10_000_000.0,
    ):
        self._strategy = strategy
        self._risk_manager = risk_manager
        self._data_source = data_source
        self._order_executor = order_executor
        self._notifier = notifier
        self._session_factory = session_factory
        self._universe = universe
        self._source_symbol = source_symbol
        self._costs = costs or TransactionCosts()
        self._initial_cash = initial_cash

    def run_once(self) -> RunSummary:
        end = date.today()  # noqa: DTZ011 — 날짜만 필요, 하루 한 번 실행 전제라 tz 무관
        start = end - timedelta(days=HISTORY_LOOKBACK_DAYS)

        latest_prices: dict[str, float] = {}
        latest_signals: dict[str, list] = {}
        run_date: date | None = None

        for ticker in self._universe:
            df = self._data_source.get_daily_ohlcv(self._source_symbol(ticker), start, end)
            if len(df) == 0:
                continue
            last_row = df.iloc[-1]
            latest_prices[ticker.symbol] = float(last_row["close"])
            run_date = last_row["trade_date"]

            signals = self._strategy.generate_signals(ticker.symbol, df)
            latest_signals[ticker.symbol] = [s for s in signals if s.trade_date == run_date]

        summary = RunSummary(run_date=run_date, checked_symbols=len(latest_prices))
        if run_date is None:
            return summary

        cash, day_start_equity = self._load_engine_state(run_date)
        positions = self._load_positions()

        # 1) 청산: 손절 우선, 그다음 전략 매도 신호
        for symbol, position in list(positions.items()):
            if symbol not in latest_prices:
                continue
            price = latest_prices[symbol]
            exit_reason = None
            if self._risk_manager.should_stop_loss(position.entry_price, price):
                exit_reason = "손절"
            else:
                for signal in latest_signals.get(symbol, []):
                    if signal.signal_type == SignalType.SELL:
                        exit_reason = signal.reason
                        break

            if exit_reason is None:
                continue

            ticker = _find_ticker(self._universe, symbol)
            order = self._order_executor.submit_order(symbol, OrderSide.SELL, position.quantity, price)
            proceeds = order.quantity * order.price * (1 - self._costs.total_sell_cost_pct)
            cash += proceeds
            del positions[symbol]
            self._record_order(order, exit_reason)
            self._delete_position(symbol)
            summary.actions.append(
                ExecutedAction(symbol, ticker.name, OrderSide.SELL, order.quantity, order.price, exit_reason)
            )
            self._notify(
                f"🔴 매도 체결\n종목: {ticker.name}({symbol})\n수량: {order.quantity}주\n"
                f"가격: {order.price:,.0f}원\n사유: {exit_reason}"
            )

        equity_after_exits = cash + sum(
            positions[s].quantity * latest_prices[s] for s in positions if s in latest_prices
        )
        daily_pnl_pct = (
            (equity_after_exits - day_start_equity) / day_start_equity if day_start_equity > 0 else 0.0
        )

        # 2) 진입: 리스크 매니저 승인을 받은 매수 신호만 실행
        for symbol, price in latest_prices.items():
            if symbol in positions:
                continue
            buy_signals = [s for s in latest_signals.get(symbol, []) if s.signal_type == SignalType.BUY]
            if not buy_signals:
                continue

            policy = self._risk_manager.get_policy()
            decision = self._risk_manager.check_new_position(
                proposed_weight=policy.max_position_weight,
                current_open_positions=len(positions),
                daily_pnl_pct=daily_pnl_pct,
            )
            ticker = _find_ticker(self._universe, symbol)
            if not decision.approved:
                summary.rejections.append(f"{ticker.name}({symbol}): {decision.reason}")
                continue

            target_value = equity_after_exits * policy.max_position_weight
            quantity = int(target_value / (price * (1 + self._costs.buy_fee_pct)))
            cost = quantity * price * (1 + self._costs.buy_fee_pct)
            if quantity <= 0 or cost > cash:
                continue

            order = self._order_executor.submit_order(symbol, OrderSide.BUY, quantity, price)
            cash -= cost
            positions[symbol] = PositionRow(
                symbol=symbol,
                quantity=order.quantity,
                entry_price=order.price,
                entry_date=run_date,
                entry_reason=buy_signals[0].reason,
            )
            self._record_order(order, buy_signals[0].reason)
            self._save_position(positions[symbol])
            summary.actions.append(
                ExecutedAction(symbol, ticker.name, OrderSide.BUY, order.quantity, order.price, buy_signals[0].reason)
            )
            self._notify(
                f"🟢 매수 체결\n종목: {ticker.name}({symbol})\n수량: {order.quantity}주\n"
                f"가격: {order.price:,.0f}원\n사유: {buy_signals[0].reason}"
            )

        final_equity = cash + sum(
            positions[s].quantity * latest_prices[s] for s in positions if s in latest_prices
        )
        # day_start_equity는 "직전 실행 종료 시점 평가금액"이다 — 하루 한 번만
        # 도는 엔진이라 이번 실행의 최종 평가금액이 곧 다음 실행의 기준점이 된다.
        self._save_engine_state(run_date, cash, final_equity)
        return summary

    def _notify(self, message: str) -> None:
        self._notifier.send(message)

    def _load_positions(self) -> dict[str, PositionRow]:
        with self._session_factory() as session:
            rows = session.query(PositionRow).all()
            session.expunge_all()
            return {row.symbol: row for row in rows}

    def _save_position(self, position: PositionRow) -> None:
        with self._session_factory() as session:
            session.merge(position)
            session.commit()

    def _delete_position(self, symbol: str) -> None:
        with self._session_factory() as session:
            row = session.get(PositionRow, symbol)
            if row is not None:
                session.delete(row)
                session.commit()

    def _record_order(self, order, reason: str) -> None:
        with self._session_factory() as session:
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

    def _load_engine_state(self, run_date: date) -> tuple[float, float]:
        """(cash, day_start_equity)를 돌려준다. day_start_equity는 '직전
        실행이 끝난 시점의 평가금액' — 하루 한 번만 도는 엔진이라 이게 곧
        오늘의 기준점(어제 종가 기준 평가금액)이 된다. 상태가 아예 없는
        첫 실행이면, 남아 있는 포지션을 진입가로 어림잡아 기준을 만든다."""
        with self._session_factory() as session:
            cash_row = session.get(EngineStateRow, "cash")
            equity_row = session.get(EngineStateRow, "day_start_equity")

            cash = float(cash_row.value) if cash_row else self._initial_cash
            if equity_row is not None:
                day_start_equity = float(equity_row.value)
            else:
                positions_value = sum(
                    p.quantity * p.entry_price for p in session.query(PositionRow).all()
                )
                day_start_equity = cash + positions_value
            return cash, day_start_equity

    def _save_engine_state(self, run_date: date, cash: float, day_start_equity: float) -> None:
        with self._session_factory() as session:
            for key, value in (
                ("cash", str(cash)),
                ("equity_date", run_date.isoformat()),
                ("day_start_equity", str(day_start_equity)),
            ):
                row = session.get(EngineStateRow, key)
                if row is None:
                    session.add(EngineStateRow(key=key, value=value))
                else:
                    row.value = value
            session.commit()


def _find_ticker(universe: list[Ticker], symbol: str) -> Ticker:
    for ticker in universe:
        if ticker.symbol == symbol:
            return ticker
    return Ticker(symbol=symbol, name=symbol, market="", yahoo_symbol="")
