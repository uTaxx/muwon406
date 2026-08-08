"""Keyword Groups 로더 — 뉴스 수집 실체화 라운드(2026-08-08) 신설.

`config/topics.yaml`의 `include_keywords`/`exclude_keywords`는 Topic 하나당 평면
리스트 1개뿐이라 "키워드를 그룹으로 나누고 그룹별로 다른 AI 지침을 준다"는 요구를
담을 수 없다. `KEYWORD_GROUPS`(Google Sheets 신설 탭, `schemas/google_sheets_columns.json`)
가 1차 진실 공급원이지만, `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`가 아직 없으므로
`config/keyword_groups.yaml`을 로컬 폴백으로 병행 설계했다 — 컬럼 구조가 동일해
Sheets가 준비되면 코드 변경 없이 `source="google_sheets"`로 전환된다.
"""
from __future__ import annotations

import json

from _common import load_yaml, project_root
from jsonschema import validate as jsonschema_validate

SCHEMAS_DIR = project_root() / "schemas"


def load_keyword_groups(source: str = "local_yaml", spreadsheet_id: str | None = None) -> list[dict]:
    """`source`: "local_yaml"(기본, Sheets 준비 전까지 사용) 또는 "google_sheets"."""
    if source == "local_yaml":
        groups = load_yaml("config/keyword_groups.yaml")["keyword_groups"]
    elif source == "google_sheets":
        groups = _load_from_google_sheets(spreadsheet_id)
    else:
        raise ValueError(f"알 수 없는 source: {source!r} (local_yaml 또는 google_sheets만 지원)")

    schema = json.loads((SCHEMAS_DIR / "keyword_group.schema.json").read_text(encoding="utf-8"))
    for group in groups:
        jsonschema_validate(instance=group, schema=schema)
    return groups


def active_keyword_groups(groups: list[dict] | None = None) -> list[dict]:
    groups = groups if groups is not None else load_keyword_groups()
    return [g for g in groups if g["enabled"]]


def _load_from_google_sheets(spreadsheet_id: str | None) -> list[dict]:
    from _common import env_or_none
    from storage.google_sheets_storage import GoogleSheetsStorage

    spreadsheet_id = spreadsheet_id or env_or_none("GOOGLE_SHEETS_MASTER_SPREADSHEET_ID")
    storage = GoogleSheetsStorage(spreadsheet_id=spreadsheet_id, enabled=True)
    rows = storage.load_all("KEYWORD_GROUPS")
    return [_row_to_group(row) for row in rows]


def _row_to_group(row: dict) -> dict:
    """Sheets 행(전부 문자열)을 keyword_group.schema.json 타입에 맞게 변환한다."""
    return {
        "group_id": row["group_id"],
        "topic_id": row["topic_id"],
        "group_name": row["group_name"],
        "include_keywords": _split_csv(row.get("include_keywords", "")),
        "exclude_keywords": _split_csv(row.get("exclude_keywords", "")),
        "ai_instructions": row.get("ai_instructions", ""),
        "sources": _split_csv(row.get("sources", "")),
        "enabled": str(row.get("enabled", "")).strip().upper() == "TRUE",
    }


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
