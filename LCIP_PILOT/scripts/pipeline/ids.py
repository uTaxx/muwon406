"""ID 생성 유틸 — ART-YYYYMMDD-NNNN / INT-YYYYMMDD-NNNN 패턴 (schemas/*.schema.json 기준)."""
from __future__ import annotations

from datetime import datetime


def next_id(prefix: str, at: datetime, existing_ids: set[str]) -> str:
    """`{prefix}-{YYYYMMDD}-{NNNN}` 형태의 다음 미사용 ID를 반환한다.

    existing_ids는 이미 발급된 ID 전체 집합(다른 날짜 포함 가능) — 같은 날짜의 최대 순번을
    찾아 +1 한다. 동시성 제어는 하지 않는다(Pilot 단일 프로세스 가정).
    """
    date_part = at.strftime("%Y%m%d")
    day_prefix = f"{prefix}-{date_part}-"
    max_seq = 0
    for existing in existing_ids:
        if existing.startswith(day_prefix):
            seq_part = existing[len(day_prefix) :]
            if seq_part.isdigit():
                max_seq = max(max_seq, int(seq_part))
    return f"{day_prefix}{max_seq + 1:04d}"
