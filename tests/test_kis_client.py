"""KIS 서버에 실제로 붙지 못하는 개발 환경에서, 최소한 요청 구성(URL·헤더·
TR_ID·바디)과 응답 파싱이 KIS Developers 문서와 어긋나지 않는지를 requests를
모킹해서 검증한다. 실제 서버 동작 자체는 검증하지 못한다 — 모의투자 계좌로
반드시 별도 확인이 필요하다."""

from datetime import date
from unittest.mock import MagicMock, patch

from muwon.data.kis_client import KISClient
from muwon.domain.types import OrderSide


def make_client(is_paper: bool = True) -> KISClient:
    client = KISClient(
        app_key="key", app_secret="secret", account_no="12345678", account_product_cd="01", is_paper=is_paper
    )
    client._access_token = "cached-token"
    client._token_expires_at = 9_999_999_999.0
    return client


@patch("muwon.data.kis_client.requests.post")
def test_ensure_token_requests_once_and_caches(mock_post):
    mock_post.return_value = MagicMock(
        json=lambda: {"access_token": "tok-abc", "expires_in": "3600"}
    )
    mock_post.return_value.raise_for_status = lambda: None

    client = KISClient(app_key="key", app_secret="secret")
    token1 = client._ensure_token()
    token2 = client._ensure_token()

    assert token1 == "tok-abc"
    assert token2 == "tok-abc"
    assert mock_post.call_count == 1  # 캐시된 토큰이 만료 전이면 재요청 안 함


@patch("muwon.data.kis_client.requests.get")
def test_get_daily_ohlcv_parses_output2(mock_get):
    mock_get.return_value = MagicMock(
        json=lambda: {
            "output2": [
                {
                    "stck_bsop_date": "20240102",
                    "stck_oprc": "70000",
                    "stck_hgpr": "71000",
                    "stck_lwpr": "69500",
                    "stck_clpr": "70500",
                    "acml_vol": "1000000",
                },
                {
                    "stck_bsop_date": "20240103",
                    "stck_oprc": "70500",
                    "stck_hgpr": "72000",
                    "stck_lwpr": "70000",
                    "stck_clpr": "71800",
                    "acml_vol": "1200000",
                },
            ]
        }
    )
    mock_get.return_value.raise_for_status = lambda: None

    client = make_client()
    df = client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))

    assert len(df) == 2
    assert list(df["trade_date"]) == [date(2024, 1, 2), date(2024, 1, 3)]
    assert df["close"].iloc[0] == 70500.0
    assert df["volume"].iloc[1] == 1200000


@patch("muwon.data.kis_client.requests.post")
def test_place_cash_order_uses_paper_buy_tr_id(mock_post):
    mock_post.return_value = MagicMock(
        json=lambda: {"rt_cd": "0", "output": {"ODNO": "ORDER123"}}
    )
    mock_post.return_value.raise_for_status = lambda: None

    client = make_client(is_paper=True)
    result = client.place_cash_order("005930", OrderSide.BUY, 10, 71000.0)

    assert result.order_id == "ORDER123"
    assert result.is_paper is True
    assert mock_post.call_args.kwargs["headers"]["tr_id"] == "VTTC0802U"
    assert mock_post.call_args.kwargs["json"]["ORD_QTY"] == "10"


@patch("muwon.data.kis_client.requests.post")
def test_place_cash_order_uses_real_sell_tr_id(mock_post):
    mock_post.return_value = MagicMock(
        json=lambda: {"rt_cd": "0", "output": {"ODNO": "ORDER456"}}
    )
    mock_post.return_value.raise_for_status = lambda: None

    client = make_client(is_paper=False)
    client.place_cash_order("005930", OrderSide.SELL, 5, 71000.0)

    assert mock_post.call_args.kwargs["headers"]["tr_id"] == "TTTC0801U"


@patch("muwon.data.kis_client.requests.post")
def test_place_cash_order_raises_on_kis_error(mock_post):
    mock_post.return_value = MagicMock(
        json=lambda: {"rt_cd": "1", "msg1": "잔고 부족"}
    )
    mock_post.return_value.raise_for_status = lambda: None

    client = make_client()
    try:
        client.place_cash_order("005930", OrderSide.BUY, 10, 71000.0)
        raise AssertionError("RuntimeError가 발생해야 한다")
    except RuntimeError as e:
        assert "잔고 부족" in str(e)
