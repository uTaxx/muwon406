"""KIS 서버에 실제로 붙지 못하는 개발 환경에서, 최소한 요청 구성(URL·헤더·
TR_ID·바디)과 응답 파싱이 KIS Developers 문서와 어긋나지 않는지를 requests를
모킹해서 검증한다. 실제 서버 동작 자체는 검증하지 못한다 — 모의투자 계좌로
반드시 별도 확인이 필요하다."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from muwon.data.kis_client import KISClient, KISOrderRejected
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
        status_code=200,
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


class FakeClock:
    """time.time()을 테스트가 제어하는 값으로 대체 — 실제로 잠들지 않고도
    요청 간격 로직(_throttle)을 검증한다."""

    def __init__(self, start: float = 1000.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@patch("muwon.data.kis_client.requests.get")
@patch("muwon.data.kis_client.time.time")
def test_throttle_waits_between_consecutive_paper_requests(mock_time, mock_get):
    """모의투자 계좌로 유니버스 종목을 연달아 조회하다 9번째 요청부터
    500이 난 실제 사고를 재현한 회귀 테스트 — 요청 간격이 0.5초보다 짧으면
    다음 요청 전에 부족한 만큼 대기해야 한다."""
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"output2": []})
    mock_get.return_value.raise_for_status = lambda: None

    clock = FakeClock()
    mock_time.side_effect = clock
    sleeps: list[float] = []

    client = make_client(is_paper=True)
    client._sleep = lambda seconds: (sleeps.append(seconds), clock.advance(seconds))[0]

    client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))
    clock.advance(0.1)  # 다음 요청 전 0.1초만 경과 — 0.5초 제한에 못 미침
    client.get_daily_ohlcv("000660", date(2024, 1, 2), date(2024, 1, 3))

    assert len(sleeps) == 1
    assert round(sleeps[0], 4) == 0.4  # 0.5 - 0.1


@patch("muwon.data.kis_client.requests.get")
@patch("muwon.data.kis_client.time.time")
def test_throttle_skips_wait_once_interval_already_elapsed(mock_time, mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"output2": []})
    mock_get.return_value.raise_for_status = lambda: None

    clock = FakeClock()
    mock_time.side_effect = clock
    sleeps: list[float] = []

    client = make_client(is_paper=True)
    client._sleep = lambda seconds: (sleeps.append(seconds), clock.advance(seconds))[0]

    client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))
    clock.advance(1.0)  # 제한(0.5초)보다 충분히 지남
    client.get_daily_ohlcv("000660", date(2024, 1, 2), date(2024, 1, 3))

    assert sleeps == []


@patch("muwon.data.kis_client.requests.get")
@patch("muwon.data.kis_client.time.time")
def test_real_trading_uses_shorter_throttle_interval_than_paper(mock_time, mock_get):
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"output2": []})
    mock_get.return_value.raise_for_status = lambda: None

    clock = FakeClock()
    mock_time.side_effect = clock
    sleeps: list[float] = []

    client = make_client(is_paper=False)
    client._sleep = lambda seconds: (sleeps.append(seconds), clock.advance(seconds))[0]

    client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))
    clock.advance(0.1)  # 실전투자 제한(0.05초)보다 지남 — 대기 불필요
    client.get_daily_ohlcv("000660", date(2024, 1, 2), date(2024, 1, 3))

    assert sleeps == []


@patch("muwon.data.kis_client.requests.get")
def test_get_daily_ohlcv_retries_on_500_then_succeeds(mock_get):
    """throttle을 둬도 산발적으로 500이 나는 걸 실제로 관찰해서 추가한
    재시도 로직 — 두 번째 시도에서 성공하면 그 결과를 그대로 써야 한다."""
    error_response = MagicMock(status_code=500)
    ok_response = MagicMock(status_code=200, json=lambda: {"output2": []})
    ok_response.raise_for_status = lambda: None
    mock_get.side_effect = [error_response, ok_response]

    client = make_client()
    client._sleep = lambda seconds: None  # 테스트에서 실제로 잠들지 않는다

    df = client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))

    assert len(df) == 0
    assert mock_get.call_count == 2


@patch("muwon.data.kis_client.requests.get")
def test_get_daily_ohlcv_gives_up_after_max_retries(mock_get):
    error_response = MagicMock(status_code=500)
    error_response.raise_for_status = MagicMock(side_effect=RuntimeError("500 Server Error"))
    mock_get.return_value = error_response

    client = make_client()
    client._sleep = lambda seconds: None

    try:
        client.get_daily_ohlcv("005930", date(2024, 1, 2), date(2024, 1, 3))
        raise AssertionError("예외가 발생해야 한다")
    except RuntimeError:
        pass

    assert mock_get.call_count == 3  # _MAX_RETRIES


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


@patch("muwon.data.kis_client.requests.post")
def test_order_rejection_exposes_kis_codes_separately_from_network_errors(mock_post):
    """KIS가 업무 규칙으로 거부한 것(요청 형식은 맞음)과 네트워크·인증
    실패(요청 자체가 틀림)를 호출부가 구분할 수 있어야 한다 — 주문 경로
    검증 스크립트가 이 구분으로 성공/실패를 판정한다."""
    mock_post.return_value = MagicMock(
        json=lambda: {"rt_cd": "1", "msg_cd": "40570000", "msg1": "장시간이 아닙니다"}
    )
    mock_post.return_value.raise_for_status = lambda: None

    client = make_client()
    with pytest.raises(KISOrderRejected) as excinfo:
        client.place_cash_order("005930", OrderSide.BUY, 1, 71000.0)

    rejection = excinfo.value
    assert rejection.rt_cd == "1"
    assert rejection.msg_cd == "40570000"
    assert rejection.msg1 == "장시간이 아닙니다"
    assert isinstance(rejection, RuntimeError)  # 기존 호출부 호환
