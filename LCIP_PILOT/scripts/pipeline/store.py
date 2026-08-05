"""Store 단계 — 검증된 레코드를 ARTICLE_DB/INTELLIGENCE_DB에 저장한다.

Round 4까지는 실제 Google Sheets API를 호출하지 않는다(CLAUDE.md 절대 원칙 #8). 이 모듈은
JSON Lines 파일을 로컬 ARTICLE_DB/INTELLIGENCE_DB의 스탠드인으로 사용해, 실제 저장 I/O와
"이미 저장된 ID/URL 조회"(Normalize의 dedup, Generate Intelligence의 ID 발급에 필요)까지
정말로 동작하게 만든다. 실제 Google Sheets 연동은 TASK-006 dry-run 도구가 승인된 뒤 이
저장소를 교체하면 된다 — Pipeline 상위 단계는 이 모듈의 함수 시그니처에만 의존한다.
"""
from __future__ import annotations

import json
from pathlib import Path


def append_record(sink_path: Path, record: dict) -> None:
    sink_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sink_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_records(sink_path: Path) -> list[dict]:
    if not sink_path.exists():
        return []
    records = []
    with open(sink_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def existing_ids(sink_path: Path, id_field: str) -> set[str]:
    return {record[id_field] for record in load_records(sink_path)}


def existing_values(sink_path: Path, field: str) -> set[str]:
    return {record[field] for record in load_records(sink_path) if record.get(field)}
