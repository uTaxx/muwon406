from datetime import date

from muwon.data.yahoo_client import YahooFinanceDataSource

SAMPLE_PAYLOAD = {
    "chart": {
        "result": [
            {
                "timestamp": [1704153600, 1704240000],  # 2024-01-02, 2024-01-03 UTC
                "indicators": {
                    "quote": [
                        {
                            "open": [71000.0, 71500.0],
                            "high": [71800.0, 72000.0],
                            "low": [70500.0, 71200.0],
                            "close": [71200.0, 71900.0],
                            "volume": [12_000_000, 10_500_000],
                        }
                    ]
                },
            }
        ],
        "error": None,
    }
}

EMPTY_PAYLOAD = {"chart": {"result": [], "error": {"code": "Not Found"}}}


def test_parse_chart_response_produces_expected_columns():
    df = YahooFinanceDataSource._parse_chart_response(SAMPLE_PAYLOAD)
    assert list(df.columns) == ["trade_date", "open", "high", "low", "close", "volume"]
    assert len(df) == 2
    assert df["trade_date"].iloc[0] == date(2024, 1, 2)
    assert df["close"].iloc[1] == 71900.0


def test_parse_chart_response_handles_empty_result():
    df = YahooFinanceDataSource._parse_chart_response(EMPTY_PAYLOAD)
    assert len(df) == 0
    assert list(df.columns) == ["trade_date", "open", "high", "low", "close", "volume"]


def test_parse_chart_response_drops_rows_with_missing_close():
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1704153600, 1704240000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [71000.0, None],
                                "high": [71800.0, None],
                                "low": [70500.0, None],
                                "close": [71200.0, None],
                                "volume": [12_000_000, None],
                            }
                        ]
                    },
                }
            ]
        }
    }
    df = YahooFinanceDataSource._parse_chart_response(payload)
    assert len(df) == 1
