import pandas as pd

from muwon.data.universe import Ticker
from muwon.db.models import OrderRow, PositionRow, TradeRow
from muwon.db.session import make_session_factory
from muwon.domain.types import OrderSide
from muwon.execution.engine import TradingEngine
from muwon.execution.simulated_executor import SimulatedOrderExecutor
from muwon.risk.manager import RiskManager
from muwon.settings.schema import RiskPolicy
from muwon.strategy.rule_based import MovingAverageRsiStrategy
from tests.price_series import breakout_entry_then_dead_cross_exit, flat_then_breakout

TEST_TICKER = Ticker("005930", "삼성전자", "KOSPI", "005930.KS")


class FakeDataSource:
    def __init__(self, frames: dict[str, pd.DataFrame] | None = None):
        self.frames = frames or {}

    def get_daily_ohlcv(self, symbol, start, end):
        return self.frames.get(symbol, pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"]))


class FakeNotifier:
    def __init__(self):
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def make_engine(data_source, policy: RiskPolicy | None = None, notifier=None, order_executor=None):
    policy = policy or RiskPolicy()
    session_factory = make_session_factory("sqlite:///:memory:")
    notifier = notifier or FakeNotifier()
    engine = TradingEngine(
        strategy=MovingAverageRsiStrategy(),
        risk_manager=RiskManager(policy_provider=lambda: policy),
        data_source=data_source,
        order_executor=order_executor or SimulatedOrderExecutor(),
        notifier=notifier,
        session_factory=session_factory,
        universe=[TEST_TICKER],
        source_symbol=lambda ticker: ticker.symbol,
    )
    return engine, session_factory, notifier


def test_buy_signal_executes_order_persists_position_and_notifies():
    df = flat_then_breakout(tail_days=0)
    data_source = FakeDataSource({TEST_TICKER.symbol: df})
    engine, session_factory, notifier = make_engine(data_source)

    summary = engine.run_once()

    assert len(summary.actions) == 1
    action = summary.actions[0]
    assert action.side == OrderSide.BUY
    assert action.symbol == TEST_TICKER.symbol

    with session_factory() as session:
        positions = session.query(PositionRow).all()
        orders = session.query(OrderRow).all()
    assert len(positions) == 1
    assert positions[0].quantity == action.quantity
    assert len(orders) == 1
    assert orders[0].side == "buy"

    assert len(notifier.messages) == 1
    assert "매수 체결" in notifier.messages[0]
    assert TEST_TICKER.name in notifier.messages[0]


def test_dead_cross_sells_existing_position_and_notifies():
    entry_df = flat_then_breakout(tail_days=0)
    data_source = FakeDataSource({TEST_TICKER.symbol: entry_df})
    engine, session_factory, notifier = make_engine(data_source)
    engine.run_once()  # 1일차: 진입

    exit_df = breakout_entry_then_dead_cross_exit(tail_days=0)
    data_source.frames[TEST_TICKER.symbol] = exit_df
    summary = engine.run_once()  # 며칠 뒤: 데드크로스로 청산

    assert len(summary.actions) == 1
    action = summary.actions[0]
    assert action.side == OrderSide.SELL
    assert action.reason == "단기선 하향이탈"

    with session_factory() as session:
        positions = session.query(PositionRow).all()
        orders = session.query(OrderRow).all()
        trades = session.query(TradeRow).all()
    assert len(positions) == 0
    assert len(orders) == 2  # 매수 1건 + 매도 1건

    assert len(trades) == 1
    assert trades[0].strategy_key == "ma_rsi_v1"
    assert trades[0].exit_reason == "단기선 하향이탈"
    assert trades[0].pnl_pct < 0  # 진입가보다 낮은 가격에 청산됐으므로 손실

    assert any("매도 체결" in m for m in notifier.messages)


def test_trading_disabled_blocks_entry_and_sends_no_notification():
    df = flat_then_breakout(tail_days=0)
    data_source = FakeDataSource({TEST_TICKER.symbol: df})
    policy = RiskPolicy(trading_enabled=False)
    engine, session_factory, notifier = make_engine(data_source, policy=policy)

    summary = engine.run_once()

    assert summary.actions == []
    assert len(summary.rejections) == 1
    assert "자동매매" in summary.rejections[0]
    assert notifier.messages == []

    with session_factory() as session:
        assert session.query(PositionRow).count() == 0


def test_stop_loss_sells_before_dead_cross_signal():
    entry_df = flat_then_breakout(tail_days=0)
    data_source = FakeDataSource({TEST_TICKER.symbol: entry_df})
    engine, _session_factory, _notifier = make_engine(data_source, policy=RiskPolicy(stop_loss_pct=-0.05))
    engine.run_once()  # 진입가 102

    crash_row = entry_df.iloc[[-1]].copy()
    crash_row["close"] = 90.0  # 진입가(102) 대비 -11.8%
    crash_row["trade_date"] = entry_df["trade_date"].iloc[-1] + pd.Timedelta(days=1)
    data_source.frames[TEST_TICKER.symbol] = pd.concat([entry_df, crash_row], ignore_index=True)

    summary = engine.run_once()

    assert len(summary.actions) == 1
    assert summary.actions[0].reason == "손절"
