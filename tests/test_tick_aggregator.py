from datetime import UTC, datetime, timedelta

from muwon.data.tick_aggregator import BarAggregator, Tick

T0 = datetime(2024, 1, 2, 9, 0, 0, tzinfo=UTC)


def tick(symbol="005930", price=100.0, volume=10, offset_seconds=0):
    return Tick(symbol=symbol, price=price, volume=volume, timestamp=T0 + timedelta(seconds=offset_seconds))


def test_ticks_within_same_window_accumulate_into_one_bar():
    agg = BarAggregator(bar_seconds=60)
    assert agg.add_tick(tick(price=100.0, volume=10, offset_seconds=0)) is None
    assert agg.add_tick(tick(price=102.0, volume=5, offset_seconds=10)) is None
    closed = agg.add_tick(tick(price=99.0, volume=7, offset_seconds=30))
    assert closed is None  # 아직 같은 60초 창 안

    open_bar = agg.force_close("005930")
    assert open_bar.open == 100.0
    assert open_bar.high == 102.0
    assert open_bar.low == 99.0
    assert open_bar.close == 99.0
    assert open_bar.volume == 22


def test_new_window_closes_previous_bar():
    agg = BarAggregator(bar_seconds=60)
    agg.add_tick(tick(price=100.0, offset_seconds=0))
    agg.add_tick(tick(price=101.0, offset_seconds=30))
    closed = agg.add_tick(tick(price=105.0, offset_seconds=65))  # 다음 60초 창

    assert closed is not None
    assert closed.close == 101.0
    assert closed.volume == 20  # 첫 두 틱의 볼륨(기본값 10)만 포함


def test_symbols_are_tracked_independently():
    agg = BarAggregator(bar_seconds=60)
    agg.add_tick(tick(symbol="005930", price=100.0, offset_seconds=0))
    agg.add_tick(tick(symbol="000660", price=200.0, offset_seconds=0))

    bar_a = agg.force_close("005930")
    bar_b = agg.force_close("000660")
    assert bar_a.close == 100.0
    assert bar_b.close == 200.0


def test_force_close_missing_symbol_returns_none():
    agg = BarAggregator(bar_seconds=60)
    assert agg.force_close("999999") is None
