"""GoogleSheetsStorage — 실제 Google Sheets(ARTICLE_DB/INTELLIGENCE_DB 탭)를 저장소로
쓰는 구현 (구조만, 이번 라운드는 미연동).

`providers/claude_provider.py`의 ClaudeProvider와 동일한 2중 안전장치 패턴이다:
`enabled=False`(기본값)면 실제 호출 이전에 명시적으로 멈춘다. `enabled=True`로 켜도
`spreadsheet_id`가 없으면 역시 멈춘다. 실제 Sheets API 호출(및 재시도/행 매핑 로직)은
TASK-010A 본구현(사용자 승인 및 Google OAuth 준비 후)에서 완성한다.
"""
from __future__ import annotations

from .base import StorageBackend, StorageBackendDisabledError


class GoogleSheetsStorage(StorageBackend):
    def __init__(self, spreadsheet_id: str | None = None, enabled: bool = False):
        self.spreadsheet_id = spreadsheet_id
        self.enabled = enabled

    def append(self, collection: str, record: dict) -> None:
        self._require_ready()
        self._call_sheets_api("append", collection)

    def load_all(self, collection: str) -> list[dict]:
        self._require_ready()
        self._call_sheets_api("load_all", collection)

    def _require_ready(self) -> None:
        if not self.enabled:
            raise StorageBackendDisabledError(
                "GoogleSheetsStorage.enabled=False — 실제 Google Sheets 호출은 TASK-010A "
                "본구현 승인 후에만 활성화한다. 지금은 LocalJSONLStorage를 사용하라."
            )
        if not self.spreadsheet_id:
            raise RuntimeError(
                "spreadsheet_id가 없다 — .env의 GOOGLE_SHEETS_MASTER_SPREADSHEET_ID를 "
                "확인해야 한다 (임의로 추정하지 않는다)."
            )

    def _call_sheets_api(self, operation: str, collection: str) -> None:
        # 실제 Google Sheets API 호출/행 매핑/재시도 로직은 TASK-010A 본구현
        # (사용자 승인 후)에서 완성한다.
        raise NotImplementedError(
            f"GoogleSheetsStorage.{operation}('{collection}') 실제 호출부는 TASK-010A "
            "본구현 대상이다."
        )
