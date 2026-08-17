from muwon.indicators.technical import add_indicators
from tests.price_series import flat_then_breakout


def test_sma_short_nan_before_window_then_populated():
    df = add_indicators(flat_then_breakout())
    assert df["sma_short"].iloc[:19].isna().all()
    assert df["sma_short"].iloc[19:].notna().all()


def test_rsi_within_bounds_once_available():
    df = add_indicators(flat_then_breakout())
    rsi = df["rsi"].dropna()
    assert len(rsi) > 0
    assert (rsi >= 0).all() and (rsi <= 100).all()


def test_volume_ma_matches_rolling_mean():
    df = add_indicators(flat_then_breakout())
    expected = df["volume"].rolling(window=20).mean()
    pd_equal = (df["volume_ma"].fillna(-1) == expected.fillna(-1)).all()
    assert pd_equal


def test_custom_windows_change_column_values():
    df_default = add_indicators(flat_then_breakout())
    df_custom = add_indicators(flat_then_breakout(), sma_short=5, sma_long=20, rsi_period=7, volume_ma_window=5)
    assert df_custom["sma_short"].iloc[:4].isna().all()
    assert df_custom["sma_short"].iloc[4:].notna().all()
    assert not df_default["sma_short"].equals(df_custom["sma_short"])
