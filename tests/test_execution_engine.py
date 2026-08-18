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


class ScriptedStrategy:
    """종목별로 지정한 점수의 매수 신호만 내는 전략 — 선택 순서 검증용."""

    name = "scripted"

    def __init__(self, scores: dict[str, float]):
        self.scores = scores

    def generate_signals(self, symbol, price_history):
        from muwon.domain.types import Signal, SignalType

        last = price_history.iloc[-1]
        return [
            Signal(
                symbol=symbol,
                trade_date=last["trade_date"],
                signal_type=SignalType.BUY,
                strategy_name=self.name,
                reason=f"점수 {self.scores[symbol]}",
                score=self.scores[symbol],
            )
        ]


def make_multi_engine(strategy, tickers, frames, policy):
    session_factory = make_session_factory("sqlite:///:memory:")
    engine = TradingEngine(
        strategy=strategy,
        risk_manager=RiskManager(policy_provider=lambda: policy),
        data_source=FakeDataSource(frames),
        order_executor=SimulatedOrderExecutor(),
        notifier=FakeNotifier(),
        session_factory=session_factory,
        universe=tickers,
        source_symbol=lambda ticker: ticker.symbol,
    )
    return engine, session_factory


def test_buys_strongest_signal_when_slots_are_scarce():
    """자리가 하나뿐인데 신호가 셋이면 '가장 강한' 걸 사야 한다.

    정렬이 없으면 유니버스 순서(=시가총액 순)대로 앞에서부터 사게 되는데,
    종목이 60개로 늘어난 뒤에는 그게 곧 '뒤쪽 종목은 영영 못 산다'는 뜻이
    된다. 그래서 일부러 가장 약한 신호를 목록 맨 앞에 둔다."""
    from tests.price_series import make_price_df

    tickers = [
        Ticker("000001", "약한신호", "KOSPI", "000001.KS"),
        Ticker("000002", "강한신호", "KOSDAQ", "000002.KQ"),
        Ticker("000003", "중간신호", "KOSPI", "000003.KS"),
    ]
    frames = {t.symbol: make_price_df([100.0] * 5) for t in tickers}
    strategy = ScriptedStrategy({"000001": 0.1, "000002": 9.9, "000003": 0.5})

    engine, _ = make_multi_engine(
        strategy, tickers, frames, RiskPolicy(max_concurrent_positions=1)
    )
    summary = engine.run_once()

    assert len(summary.actions) == 1
    assert summary.actions[0].symbol == "000002"  # 목록상 두 번째지만 가장 강하다


def test_equal_scores_keep_universe_order():
    """점수가 같으면 기존 순서를 유지해야 한다 — 정렬 도입으로 기존 동작이
    엉뚱하게 바뀌지 않는지 확인한다."""
    from tests.price_series import make_price_df

    tickers = [
        Ticker("000001", "첫째", "KOSPI", "000001.KS"),
        Ticker("000002", "둘째", "KOSPI", "000002.KS"),
    ]
    frames = {t.symbol: make_price_df([100.0] * 5) for t in tickers}
    strategy = ScriptedStrategy({"000001": 0.0, "000002": 0.0})

    engine, _ = make_multi_engine(
        strategy, tickers, frames, RiskPolicy(max_concurrent_positions=1)
    )
    summary = engine.run_once()

    assert summary.actions[0].symbol == "000001"


def test_ignores_todays_incomplete_bar():
    """장중에 돌면 오늘 봉은 거래량이 덜 쌓이고 종가도 확정 전이다.
    그 봉으로 판단하면 '거래량 2배 급증' 같은 조건이 성립할 수 없으므로,
    마지막으로 완성된 일봉까지만 써야 한다."""
    from datetime import date, timedelta

    from tests.price_series import make_price_df

    as_of = date(2026, 8, 18)
    ticker = Ticker("000001", "테스트", "KOSPI", "000001.KS")
    # 마지막 두 봉의 종가를 다르게 둬서 어느 봉을 썼는지 가격으로 구분한다
    df = make_price_df([100.0, 100.0, 100.0, 111.0, 999.0], start=as_of - timedelta(days=4))
    assert df["trade_date"].iloc[-1] == as_of  # 마지막 봉이 '오늘'

    engine, _ = make_multi_engine(
        ScriptedStrategy({"000001": 1.0}), [ticker], {ticker.symbol: df}, RiskPolicy()
    )
    summary = engine.run_once(as_of=as_of)

    assert summary.run_date == as_of - timedelta(days=1)
    assert summary.actions[0].price == 111.0  # 오늘(999)이 아니라 어제 종가로 판단


def test_active_strategy_scores_its_buy_signals():
    """점수 매기기가 실제 전략에 반영돼 있어야 정렬이 의미를 갖는다.
    전부 0이면 정렬은 그냥 기존 순서와 같아진다."""
    from muwon.domain.types import SignalType
    from muwon.strategy.registry import build_strategy

    df = flat_then_breakout(tail_days=0)
    buys = [
        s
        for s in build_strategy("ma_rsi_v1").generate_signals("005930", df)
        if s.signal_type == SignalType.BUY
    ]

    assert buys, "매수 신호가 없으면 이 테스트는 아무것도 검증하지 못한다"
    assert all(s.score > 0 for s in buys)
