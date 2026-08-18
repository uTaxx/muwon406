"""포트폴리오 단위 백테스트 엔진.

여러 종목을 하나의 계좌(현금+포지션)로 묶어서 하루 단위로 시뮬레이션한다.
종목별로 따로 백테스트하지 않는 이유는, RiskManager가 검증하는 규칙(종목당
비중/동시보유종목수/일일손실한도)이 애초에 포트폴리오 전체를 보는 값이라
개별 종목 단위로는 의미가 없기 때문이다. 실거래 실행기(execution/)가 훗날
따라야 할 흐름(신호 생성 → 리스크 매니저 승인 → 주문)과 최대한 같은 순서로
짜서, 백테스트와 실거래 로직이 어긋나지 않게 한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from muwon.backtest.costs import TransactionCosts
from muwon.domain.interfaces import Strategy
from muwon.domain.types import SignalType
from muwon.indicators.technical import add_indicators
from muwon.risk.manager import RiskManager
from muwon.strategy.portfolio import (
    MarketContext,
    PortfolioStrategy,
    as_portfolio_strategy,
    bars_since,
)


@dataclass
class OpenPosition:
    symbol: str
    quantity: int
    entry_price: float
    entry_date: date
    entry_reason: str = ""


@dataclass
class ClosedTrade:
    symbol: str
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: int
    pnl_pct: float
    pnl_amount: float
    exit_reason: str
    entry_reason: str = ""


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame  # columns: trade_date, equity
    closed_trades: list[ClosedTrade] = field(default_factory=list)
    final_positions: dict[str, OpenPosition] = field(default_factory=dict)

    @property
    def final_equity(self) -> float:
        return float(self.equity_curve["equity"].iloc[-1]) if len(self.equity_curve) else 0.0

    @property
    def total_return_pct(self) -> float:
        if len(self.equity_curve) < 1:
            return 0.0
        start = float(self.equity_curve["equity"].iloc[0])
        end = float(self.equity_curve["equity"].iloc[-1])
        return (end / start - 1) * 100 if start > 0 else 0.0

    @property
    def max_drawdown_pct(self) -> float:
        if len(self.equity_curve) < 2:
            return 0.0
        equity = self.equity_curve["equity"]
        running_peak = equity.cummax()
        drawdown = (equity - running_peak) / running_peak
        return float(drawdown.min() * 100)

    @property
    def win_rate_pct(self) -> float:
        if not self.closed_trades:
            return 0.0
        wins = sum(1 for t in self.closed_trades if t.pnl_amount > 0)
        return wins / len(self.closed_trades) * 100

    @property
    def num_trades(self) -> int:
        return len(self.closed_trades)


class BacktestEngine:
    def __init__(
        self,
        strategy: Strategy | PortfolioStrategy,
        risk_manager: RiskManager,
        costs: TransactionCosts | None = None,
        initial_cash: float = 10_000_000.0,
    ):
        self._strategy = as_portfolio_strategy(strategy)
        self._risk_manager = risk_manager
        self._costs = costs or TransactionCosts()
        self._initial_cash = initial_cash

    def run(
        self, price_histories: dict[str, pd.DataFrame], trade_from: date | None = None
    ) -> BacktestResult:
        """price_histories: {symbol: DataFrame[trade_date, open, high, low, close, volume]}

        trade_from을 주면 그 날짜부터만 매매하고, 그 이전 구간은 지표 예열에만
        쓴다(신호는 전체 히스토리로 계산되므로 이동평균·RSI가 충분히 채워진
        상태로 매매를 시작한다). 기간을 잘라 여러 구간에서 검증할 때 필요하다 —
        예열 없이 잘라 넣으면 각 구간 초반의 지표가 NaN이라 신호가 안 나와
        짧은 구간일수록 결과가 과소평가된다."""
        enriched = {
            symbol: add_indicators(df).set_index("trade_date")
            for symbol, df in price_histories.items()
            if len(df) > 0
        }
        self._strategy.prepare(price_histories)
        trade_dates_by_symbol = {symbol: list(df.index) for symbol, df in enriched.items()}
        max_holding_days = self._strategy.max_holding_days

        all_dates = sorted({d for df in enriched.values() for d in df.index})

        cash = self._initial_cash
        positions: dict[str, OpenPosition] = {}
        closed_trades: list[ClosedTrade] = []
        equity_curve_rows: list[dict] = []
        day_start_equity = self._initial_cash

        for current_date in all_dates:
            if trade_from is not None and current_date < trade_from:
                continue  # 지표 예열 구간 — 매매도 평가금액 기록도 하지 않는다

            closes_today = {
                symbol: df.loc[current_date, "close"]
                for symbol, df in enriched.items()
                if current_date in df.index
            }

            signals_today: dict[str, list] = {}
            for signal in self._strategy.evaluate(
                MarketContext(
                    as_of=current_date,
                    histories=price_histories,
                    held=frozenset(positions),
                )
            ):
                signals_today.setdefault(signal.symbol, []).append(signal)

            # 1) 청산: 손절 → 보유기간 초과 → 전략 매도 신호
            for symbol in list(positions.keys()):
                if symbol not in closes_today:
                    continue
                price = float(closes_today[symbol])
                position = positions[symbol]
                exit_reason = None

                if self._risk_manager.should_stop_loss(position.entry_price, price):
                    exit_reason = "손절"
                elif max_holding_days is not None and bars_since(
                    trade_dates_by_symbol.get(symbol, []), position.entry_date, current_date
                ) >= max_holding_days:
                    exit_reason = f"보유 {max_holding_days}일 경과 청산"
                else:
                    for signal in signals_today.get(symbol, []):
                        if signal.signal_type == SignalType.SELL:
                            exit_reason = signal.reason
                            break

                if exit_reason is not None:
                    cash += self._close_position(position, price, current_date, exit_reason, closed_trades)
                    del positions[symbol]

            # 2) 이 시점 평가금액 → 오늘 손익률 계산
            equity_after_exits = cash + sum(
                positions[s].quantity * float(closes_today[s])
                for s in positions
                if s in closes_today
            )
            daily_pnl_pct = (
                (equity_after_exits - day_start_equity) / day_start_equity
                if day_start_equity > 0
                else 0.0
            )

            # 3) 진입: 리스크 매니저 승인을 받은 매수 신호만 실행
            for symbol, price in closes_today.items():
                if symbol in positions:
                    continue
                buy_signals = [
                    s for s in signals_today.get(symbol, []) if s.signal_type == SignalType.BUY
                ]
                if not buy_signals:
                    continue

                policy = self._risk_manager.get_policy()
                decision = self._risk_manager.check_new_position(
                    proposed_weight=policy.max_position_weight,
                    current_open_positions=len(positions),
                    daily_pnl_pct=daily_pnl_pct,
                )
                if not decision.approved:
                    continue

                price = float(price)
                target_value = equity_after_exits * policy.max_position_weight
                quantity = int(target_value / (price * (1 + self._costs.buy_fee_pct)))
                cost = quantity * price * (1 + self._costs.buy_fee_pct)
                if quantity <= 0 or cost > cash:
                    continue

                cash -= cost
                positions[symbol] = OpenPosition(
                    symbol=symbol,
                    quantity=quantity,
                    entry_price=price,
                    entry_date=current_date,
                    entry_reason=buy_signals[0].reason,
                )

            equity = cash + sum(
                positions[s].quantity * float(closes_today[s])
                for s in positions
                if s in closes_today
            )
            equity_curve_rows.append({"trade_date": current_date, "equity": equity})
            day_start_equity = equity

        equity_curve = pd.DataFrame(equity_curve_rows)
        return BacktestResult(
            equity_curve=equity_curve, closed_trades=closed_trades, final_positions=positions
        )

    def _close_position(
        self,
        position: OpenPosition,
        exit_price: float,
        exit_date: date,
        exit_reason: str,
        closed_trades: list[ClosedTrade],
    ) -> float:
        proceeds = position.quantity * exit_price * (1 - self._costs.total_sell_cost_pct)
        cost_basis = position.quantity * position.entry_price
        pnl_amount = proceeds - cost_basis
        pnl_pct = (exit_price / position.entry_price - 1) * 100 if position.entry_price > 0 else 0.0
        closed_trades.append(
            ClosedTrade(
                symbol=position.symbol,
                entry_date=position.entry_date,
                exit_date=exit_date,
                entry_price=position.entry_price,
                exit_price=exit_price,
                quantity=position.quantity,
                pnl_pct=pnl_pct,
                pnl_amount=pnl_amount,
                exit_reason=exit_reason,
                entry_reason=position.entry_reason,
            )
        )
        return proceeds
