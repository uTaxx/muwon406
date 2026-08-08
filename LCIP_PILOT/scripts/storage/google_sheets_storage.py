"""GoogleSheetsStorage — 실제 Google Sheets(ARTICLE_DB/INTELLIGENCE_DB 등 탭)를
저장소로 쓰는 구현.

`providers/claude_provider.py`의 ClaudeProvider와 동일한 2중 안전장치 패턴이다:
`enabled=False`(기본값)면 실제 호출 이전에 명시적으로 멈춘다. `enabled=True`로 켜도
`spreadsheet_id`가 없으면 역시 멈춘다.

Architect Review Round 13(RC2 실체화) — 실제 읽기/쓰기 경로를 완성했다.
`create_google_sheets.py`가 이미 참조하던 gspread를 그대로 재사용하고(새 라이브러리
도입 없음), 인증은 `scripts/google_auth.py`(Drive/Sheets/Gmail 공용 헬퍼)를 거친다.
`collection`(예: "ARTICLE_DB")은 탭 이름과 그대로 대응한다 — 탭 자체는
`create_google_sheets.py --apply`로 미리 만들어져 있어야 한다(이 클래스는 탭을
새로 만들지 않는다, 데이터 저장 책임과 스키마/구조 책임을 분리).

`client_factory`를 주입하면(테스트용) 실제 Google 인증/네트워크 없이 append/load_all
의 행 매핑 로직만 검증할 수 있다 — `GoogleRSSAdapter`의 `http_get` 주입과 동일한
패턴이다.
"""
from __future__ import annotations

from typing import Callable

from .base import StorageBackend, StorageBackendDisabledError


class GoogleSheetsStorage(StorageBackend):
    def __init__(
        self,
        spreadsheet_id: str | None = None,
        enabled: bool = False,
        auth_mode: str = "oauth_desktop",
        client_factory: Callable[[], object] | None = None,
    ):
        self.spreadsheet_id = spreadsheet_id
        self.enabled = enabled
        self.auth_mode = auth_mode
        self._client_factory = client_factory
        self._client = None

    def append(self, collection: str, record: dict) -> None:
        worksheet = self._worksheet(collection)
        headers = worksheet.row_values(1)
        if not headers:
            headers = list(record.keys())
            worksheet.append_row(headers)
        worksheet.append_row([str(record.get(h, "")) for h in headers])

    def load_all(self, collection: str) -> list[dict]:
        worksheet = self._worksheet(collection)
        return worksheet.get_all_records()

    def _worksheet(self, collection: str):
        self._require_ready()
        client = self._get_client()
        spreadsheet = client.open_by_key(self.spreadsheet_id)

        import gspread.exceptions

        try:
            return spreadsheet.worksheet(collection)
        except gspread.exceptions.WorksheetNotFound as exc:
            raise RuntimeError(
                f"Google Sheets에 '{collection}' 탭이 없다 — 먼저 "
                "`python scripts/create_google_sheets.py --apply`로 탭을 생성해야 한다."
            ) from exc

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self._client_factory is not None:
            self._client = self._client_factory()
            return self._client

        import gspread

        from google_auth import SHEETS_SCOPES, load_credentials

        creds = load_credentials(self.auth_mode, SHEETS_SCOPES)
        self._client = gspread.authorize(creds)
        return self._client

    def _require_ready(self) -> None:
        if not self.enabled:
            raise StorageBackendDisabledError(
                "GoogleSheetsStorage.enabled=False — 실제 Google Sheets 호출은 "
                "feature_flags.google_sheets_enabled와 Credential 준비 후에만 켠다. "
                "지금은 LocalJSONLStorage를 사용하라."
            )
        if not self.spreadsheet_id:
            raise RuntimeError(
                "spreadsheet_id가 없다 — .env의 GOOGLE_SHEETS_MASTER_SPREADSHEET_ID를 "
                "확인해야 한다 (임의로 추정하지 않는다)."
            )
