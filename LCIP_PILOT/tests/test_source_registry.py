"""Round 6 TASK-K03 — Source Registry 실사용 수준 검증.

`config/sources.yaml`이 Google RSS/Naver/DART/KRX/SEC/EDINET/SEDAR+/Companies House를
전부 포함하고, 각 Source가 authentication/rate_limit 필드를 갖는지 확인한다.
"""
from __future__ import annotations

from _common import load_yaml

SOURCES = load_yaml("config/sources.yaml")["sources"]
SOURCES_BY_ID = {s["source_id"]: s for s in SOURCES}


def test_source_registry_includes_all_k03_required_systems():
    names = {s["source_name"] for s in SOURCES}
    assert any("Google News RSS" in n for n in names)
    assert any("Naver" in n for n in names)
    assert any("DART" in n for n in names)
    assert any("KRX" in n for n in names)
    assert any("SEC EDGAR" in n for n in names)
    assert any("EDINET" in n for n in names)
    assert any("SEDAR" in n for n in names)
    assert any("Companies House" in n for n in names)
    assert any("정부" in n for n in names)  # 정부 RSS 카테고리
    assert any("IR" in n for n in names)  # 기업 IR 카테고리


def test_every_source_has_authentication_and_rate_limit_fields():
    required_keys = {"authentication", "rate_limit"}
    for source in SOURCES:
        missing = required_keys - source.keys()
        assert not missing, f"{source['source_id']}에 누락된 필드: {missing}"
        assert source["authentication"], f"{source['source_id']}의 authentication이 비어있다"
        assert source["rate_limit"], f"{source['source_id']}의 rate_limit이 비어있다"


def test_no_duplicate_source_ids():
    ids = [s["source_id"] for s in SOURCES]
    assert len(ids) == len(set(ids))


def test_sec_edgar_confirmed_rate_limit():
    """Round 6 리서치로 확인된 사실: SEC EDGAR는 API Key 없이 User-Agent 헤더만
    요구하며, 공식 Fair Access 정책상 초당 10 요청이다."""
    sec = SOURCES_BY_ID["SRC-0006"]
    assert "10" in sec["rate_limit"]
    assert "User-Agent" in sec["authentication"]


def test_dart_and_naver_confirmed_rate_limits():
    dart = SOURCES_BY_ID["SRC-0004"]
    naver = SOURCES_BY_ID["SRC-0003"]
    assert "10,000" in dart["rate_limit"]
    assert "25,000" in naver["rate_limit"]


def test_every_source_has_round7_fields():
    """Round 7 지시: 각 Source마다 Estimated Update Delay/Typical Reliability/
    Historical Stability를 추가한다."""
    required_keys = {"estimated_update_delay", "typical_reliability", "historical_stability"}
    for source in SOURCES:
        missing = required_keys - source.keys()
        assert not missing, f"{source['source_id']}에 누락된 Round 7 필드: {missing}"
        for key in required_keys:
            assert source[key], f"{source['source_id']}의 {key}가 비어있다"


def test_historical_stability_honestly_reports_no_pilot_history():
    """feature_flags.real_network_calls가 여전히 false인 동안, Pilot 자체 연동 이력은
    존재할 수 없다 — 임의로 안정적이라고 추정하지 않는다."""
    for source in SOURCES:
        assert "이력 없음" in source["historical_stability"]


def test_reliability_grade_still_uses_single_source_of_truth():
    """Round 6 지시: 중복 구조를 만들지 않는다 — 세분화된 1~5점 점수는
    scripts/source_priority.py가 source_type 기준으로 동적으로 계산하며, 이 YAML에
    숫자를 다시 저장하지 않는다."""
    from source_priority import score_for_source_type

    for source in SOURCES:
        assert source["reliability_grade"] in ("A", "B", "C")
        # source_type 기반 1~5점 조회가 예외 없이 동작하는지만 확인한다(중복 저장 없음 검증).
        score = score_for_source_type(source["source_type"])
        assert 1 <= score <= 5
