from muwon.indicators.technical import add_indicators
from tests.price_series import flat_then_breakout


def test_sma20_nan_before_window_then_populated():
    df = add_indicators(flat_then_breakout())
    assert df["sma20"].iloc[:19].isna().all()
    assert df["sma20"].iloc[19:].notna().all()


def test_rsi_within_bounds_once_available():
    df = add_indicators(flat_then_breakout())
    rsi = df["rsi14"].dropna()
    assert len(rsi) > 0
    assert (rsi >= 0).all() and (rsi <= 100).all()


def test_volume_ma20_matches_rolling_mean():
    df = add_indicators(flat_then_breakout())
    expected = df["volume"].rolling(window=20).mean()
    pd_equal = (df["volume_ma20"].fillna(-1) == expected.fillna(-1)).all()
    assert pd_equal
