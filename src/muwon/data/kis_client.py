"""한국투자증권(KIS) Developers API 클라이언트.

Phase 0 시점에는 앱키가 아직 없으므로 인증/시세조회/주문 메서드는
스켈레톤 상태다. Phase 1에서 실제 앱키로 KIS Developers 최신 문서
(https://apiportal.koreainvestment.com) 기준 엔드포인트를 검증하며 구현을
완성한다.

REAL_BASE_URL / PAPER_BASE_URL은 KIS Developers 공식 문서에 명시된
실전투자/모의투자 도메인이다. 실제 연동 전 반드시 최신 문서와 대조할 것.
"""

from __future__ import annotations

import time

import requests

from muwon.domain.interfaces import MarketDataSource
from muwon.settings.service import SettingsService

REAL_BASE_URL = "https://openapi.koreainvestment.com:9443"
PAPER_BASE_URL = "https://openapivts.koreainvestment.com:29443"


class KISClient(MarketDataSource):
    def __init__(self, app_key: str, app_secret: str, is_paper: bool = True):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = PAPER_BASE_URL if is_paper else REAL_BASE_URL
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    @classmethod
    def from_settings(cls, settings_service: SettingsService) -> KISClient:
        """SettingsService(=DB, 대시보드/CLI로 갱신됨)에서 현재 인증정보를
        읽어 클라이언트를 만든다. 인증정보가 바뀔 수 있으므로 오래 붙들고
        쓰지 말고, 필요할 때마다(예: 스케줄 작업 시작 시) 새로 생성할 것."""
        creds = settings_service.get_kis_credentials()
        return cls(app_key=creds.app_key, app_secret=creds.app_secret, is_paper=not creds.is_real)

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

    def get_daily_ohlcv(self, symbol, start, end):
        raise NotImplementedError(
            "Phase 1에서 구현 예정: /uapi/domestic-stock/v1/quotations/"
            "inquire-daily-itemchartprice 엔드포인트로 일봉 조회"
        )
