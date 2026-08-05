"""LocalJSONLStorage — StorageBackend의 로컬 파일 구현.

Round 4까지 `scripts/pipeline/store.py`가 하던 일(JSON Lines 파일을 ARTICLE_DB/
INTELLIGENCE_DB의 dry-run 스탠드인으로 사용)을 그대로 StorageBackend 계약으로 옮긴 것이다.
실제 외부 쓰기 없이 Pipeline을 완전히 동작시킬 수 있는 기본 구현이며, Pilot의 기본값이다.

Round 6 데드코드 정리: `scripts/pipeline/store.py`(하위호환용 래퍼)는 실제로는 자기 자신의
단위 테스트 외에 호출자가 없어(demo_pilot.py 등은 이 클래스를 직접 쓴다) 완전히 삭제했다 —
저장 로직은 이제 이 파일 하나에만 존재한다.
"""
from __future__ import annotations

import json
from pathlib import Path

from .base import StorageBackend


class LocalJSONLStorage(StorageBackend):
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def _path(self, collection: str) -> Path:
        return self.base_dir / f"{collection}.jsonl"

    def append(self, collection: str, record: dict) -> None:
        path = self._path(collection)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load_all(self, collection: str) -> list[dict]:
        path = self._path(collection)
        if not path.exists():
            return []
        records = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
