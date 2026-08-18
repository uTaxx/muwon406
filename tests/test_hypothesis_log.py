"""가설 기록 검증.

이 기록의 값어치는 '기각된 가설이 남아 있다'는 데 있다. 같은 걸 두 번
시험하지 않으려면 실패가 보여야 한다. 그래서 칸이 조용히 비거나 사라지는
경우를 막는다."""

import json

import pytest

from muwon.cloud.hypothesis_log import HypothesisRow, header_row, rows_from_json


def test_every_column_has_a_human_readable_name():
    """이 시트를 읽는 사람이 코드를 안 볼 수도 있다."""
    names = header_row()

    assert names[:3] == ["날짜", "무엇을 알고 싶었나", "가설"]
    assert "판정" in names
    assert "그래서 뭘 바꿨나" in names
    assert all("_" not in name for name in names), "밑줄이 그대로 보이면 안 된다"


def test_row_values_line_up_with_the_header():
    """칸 순서가 어긋나면 내용이 옆 칸으로 밀린다."""
    row = HypothesisRow(날짜="2026-08-18", 가설="이럴 것이다", 판정="기각")

    values = row.as_values()

    assert len(values) == len(header_row())
    assert values[header_row().index("가설")] == "이럴 것이다"
    assert values[header_row().index("판정")] == "기각"


def test_unknown_column_is_reported_not_dropped(tmp_path):
    """오타 하나로 내용이 통째로 빠지면 기록의 뜻이 없다."""
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([{"가설": "무엇", "판정결과": "기각"}]), encoding="utf-8")

    with pytest.raises(SystemExit, match="판정결과"):
        rows_from_json(str(path))


def test_backfill_file_parses_and_keeps_the_rejections():
    """저장소에 넣어 둔 지난 기록이 실제로 읽히는지, 그리고 기각된 가설이
    빠지지 않았는지 확인한다."""
    rows = rows_from_json("docs/가설기록.json")

    assert len(rows) >= 10
    assert sum(1 for r in rows if r.판정 == "기각") >= 5
    assert all(r.가설 and r.판정 and r.어떻게_확인했나 for r in rows), (
        "가설·판정·확인 방법이 빈 줄은 기록으로 쓸모가 없다"
    )
