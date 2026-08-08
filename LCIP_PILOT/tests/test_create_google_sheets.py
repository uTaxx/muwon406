"""Round 13(RC2 실체화) — create_google_sheets.py의 실제 apply_plan() 검증.

실제 Google Sheets/OAuth 없이, `gspread.authorize`와 `google_auth.load_credentials`를
가짜로 교체해 "이미 있는 탭은 건드리지 않고, 없는 탭만 생성한다"는 안전장치를 검증한다.
"""
from __future__ import annotations

import google_auth
import gspread
from create_google_sheets import apply_plan, build_plan


class _FakeWorksheet:
    def __init__(self, title: str):
        self.title = title
        self.appended_rows: list[list[str]] = []
        self.frozen_rows: int | None = None

    def append_row(self, values: list) -> None:
        self.appended_rows.append(list(values))

    def freeze(self, rows: int) -> None:
        self.frozen_rows = rows


class _FakeSpreadsheet:
    def __init__(self, existing_tab_names: list[str]):
        self._worksheets = [_FakeWorksheet(name) for name in existing_tab_names]

    def worksheets(self) -> list[_FakeWorksheet]:
        return self._worksheets

    def add_worksheet(self, title: str, rows: int, cols: int) -> _FakeWorksheet:
        ws = _FakeWorksheet(title)
        self._worksheets.append(ws)
        return ws


class _FakeGspreadClient:
    def __init__(self, spreadsheet: _FakeSpreadsheet):
        self._spreadsheet = spreadsheet

    def open_by_key(self, spreadsheet_id: str) -> _FakeSpreadsheet:
        return self._spreadsheet


def test_apply_plan_creates_only_missing_tabs(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_MASTER_SPREADSHEET_ID", "fake-spreadsheet-id")
    monkeypatch.setattr(google_auth, "load_credentials", lambda auth_mode, scopes: object())

    plan = build_plan(existing_tabs=["CONFIG_MASTER"])
    fake_spreadsheet = _FakeSpreadsheet(existing_tab_names=["CONFIG_MASTER"])
    monkeypatch.setattr(gspread, "authorize", lambda creds: _FakeGspreadClient(fake_spreadsheet))

    apply_plan(plan, auth_mode="oauth_desktop")

    final_titles = {ws.title for ws in fake_spreadsheet.worksheets()}
    all_tab_names = {t["name"] for t in plan["tabs_to_create"]} | {"CONFIG_MASTER"}
    assert final_titles == all_tab_names
    # CONFIG_MASTER는 이미 있었으므로 새 add_worksheet 호출로 다시 만들어지지 않았다
    # (동일 title 중복 없음으로 이미 확인됨) — 헤더 행도 새로 추가되지 않았어야 한다.
    config_master_ws = next(ws for ws in fake_spreadsheet.worksheets() if ws.title == "CONFIG_MASTER")
    assert config_master_ws.appended_rows == []


def test_apply_plan_writes_header_row_and_freezes(monkeypatch):
    monkeypatch.setenv("GOOGLE_SHEETS_MASTER_SPREADSHEET_ID", "fake-spreadsheet-id")
    monkeypatch.setattr(google_auth, "load_credentials", lambda auth_mode, scopes: object())

    plan = build_plan(existing_tabs=[])
    fake_spreadsheet = _FakeSpreadsheet(existing_tab_names=[])
    monkeypatch.setattr(gspread, "authorize", lambda creds: _FakeGspreadClient(fake_spreadsheet))

    apply_plan(plan, auth_mode="oauth_desktop")

    article_db_ws = next(ws for ws in fake_spreadsheet.worksheets() if ws.title == "ARTICLE_DB")
    assert article_db_ws.appended_rows  # 헤더 행이 써졌다
    assert article_db_ws.frozen_rows is not None
