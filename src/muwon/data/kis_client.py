"""한국투자증권(KIS) Developers API 클라이언트.

REAL_BASE_URL / PAPER_BASE_URL은 KIS Developers 공식 문서에 명시된
실전투자/모의투자 도메인이다. 두 도메인 모두 비표준 포트(9443/29443)를 쓰는데,
egress 정책에 따라 이 포트들이 막혀 있으면 이 클래스는 애초에 서버에 닿지
못한다 — 개발 중엔 백테스트/드라이런 전용인 YahooFinanceDataSource +
SimulatedOrderExecutor로 파이프라인을 검증하고, 이 클래스는 실제 KIS
네트워크 접근이 되는 환경(운영 서버 등)에서 실거래/모의투자로 전환할 때
쓴다.

엔드포인트/TR_ID는 KIS Developers 포털(https://apiportal.koreainvestment.com)
문서 기준으로 작성했지만, 이 개발 환경에서는 KIS 서버에 접근할 수 없어
실제 호출로 검증하지 못했다 — 실거래 전환 전 반드시 최신 문서와 대조하고
모의투자 계좌로 먼저 검증할 것.
"""

from __future__ import annotations

import time
from datetime import date

import pandas as pd
import requests

from muwon.domain.interfaces import MarketDataSource
from muwon.domain.types import OrderResult, OrderSide
from muwon.settings.service import SettingsService

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"

# 국내주식 현금주문 TR_ID — 모의투자(V)와 실전투자(T)가 서로 다르다.
_BUY_TR_ID = {"paper": "VTTC0802U", "real": "TTTC0802U"}
_SELL_TR_ID = {"paper": "VTTC0801U", "real": "TTTC0801U"}
_MARKET_ORDER_DVSN = "01"  # 시장가


class KISClient(MarketDataSource):
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str = "",
        account_product_cd: str = "01",
        is_paper: bool = True,
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.account_product_cd = account_product_cd
        self.is_paper = is_paper
        self.base_url = PAPER_BASE_URL if is_paper else REAL_BASE_URL
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    @classmethod
    def from_settings(cls, settings_service: SettingsService) -> KISClient:
        """SettingsService(=DB, 대시보드/CLI로 갱신됨)에서 현재 인증정보를
        읽어 클라이언트를 만든다. 인증정보가 바뀔 수 있으므로 오래 붙들고
        쓰지 말고, 필요할 때마다(예: 스케줄 작업 시작 시) 새로 생성할 것."""
        creds = settings_service.get_kis_credentials()
        return cls(
            app_key=creds.app_key,
            app_secret=creds.app_secret,
            account_no=creds.account_no,
            account_product_cd=creds.account_product_cd,
            is_paper=not creds.is_real,
        )

    def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        response = requests.post(
            f"{self.base_url}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.app_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + int(payload["expires_in"]) - 60
        return self._access_token

    def _auth_headers(self, tr_id: str) -> dict:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._ensure_token()}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
        }

    def get_daily_ohlcv(self, symbol: str, start: date, end: date) -> pd.DataFrame:
        response = requests.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers=self._auth_headers("FHKST03010100"),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": start.strftime("%Y%m%d"),
                "FID_INPUT_DATE_2": end.strftime("%Y%m%d"),
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("output2") or []
        if not rows:
            return pd.DataFrame(columns=["trade_date", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(
            {
                "trade_date": [
                    date(int(r["stck_bsop_date"][:4]), int(r["stck_bsop_date"][4:6]), int(r["stck_bsop_date"][6:8]))
                    for r in rows
                ],
                "open": [float(r["stck_oprc"]) for r in rows],
                "high": [float(r["stck_hgpr"]) for r in rows],
                "low": [float(r["stck_lwpr"]) for r in rows],
                "close": [float(r["stck_clpr"]) for r in rows],
                "volume": [int(r["acml_vol"]) for r in rows],
            }
        )
        return df.sort_values("trade_date").reset_index(drop=True)

    def place_cash_order(
        self, symbol: str, side: OrderSide, quantity: int, reference_price: float
    ) -> OrderResult:
        """시장가 현금주문. reference_price는 실제 체결가가 아니라, 우리
        쪽 기록/알림에 쓸 기준가(직전 종가)다 — 체결가는 별도 주문조회
        API로 확인해야 하며 이 MVP는 그 조회를 하지 않는다."""
        env = "paper" if self.is_paper else "real"
        tr_id = _BUY_TR_ID[env] if side == OrderSide.BUY else _SELL_TR_ID[env]

        response = requests.post(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash",
            headers=self._auth_headers(tr_id),
            json={
                "CANO": self.account_no,
                "ACNT_PRDT_CD": self.account_product_cd,
                "PDNO": symbol,
                "ORD_DVSN": _MARKET_ORDER_DVSN,
                "ORD_QTY": str(quantity),
                "ORD_UNPR": "0",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("rt_cd") != "0":
            raise RuntimeError(f"KIS 주문 실패: {payload.get('msg1', payload)}")

        return OrderResult(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=reference_price,
            order_id=payload["output"]["ODNO"],
            is_paper=self.is_paper,
        )
