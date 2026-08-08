from notifiers import build_digest_message
from pipeline.build_digest import build_digest_body, build_digest_subject, select_digest_records

URGENT_ARTICLE = {"title_original": "신규 소송 제기"}
URGENT_INTELLIGENCE = {
    "importance_level": "긴급",
    "lx_impact": ["LX Hausys 관련 소송 확대 가능성"],
    "recommended_actions": ["법무팀 즉시 검토"],
}
IMPORTANT_ARTICLE = {"title_original": "규제 초안 공청회"}
IMPORTANT_INTELLIGENCE = {
    "importance_level": "중요",
    "lx_impact": [],
    "recommended_actions": [],
}
REFERENCE_ARTICLE = {"title_original": "업계 일반 동향"}
REFERENCE_INTELLIGENCE = {"importance_level": "참고", "lx_impact": [], "recommended_actions": []}


def test_select_digest_records_excludes_reference_level():
    records = [
        (URGENT_ARTICLE, URGENT_INTELLIGENCE),
        (REFERENCE_ARTICLE, REFERENCE_INTELLIGENCE),
        (IMPORTANT_ARTICLE, IMPORTANT_INTELLIGENCE),
    ]
    selected = select_digest_records(records)
    assert [a["title_original"] for a, _ in selected] == ["신규 소송 제기", "규제 초안 공청회"]


def test_select_digest_records_urgent_sorted_before_important():
    records = [(IMPORTANT_ARTICLE, IMPORTANT_INTELLIGENCE), (URGENT_ARTICLE, URGENT_INTELLIGENCE)]
    selected = select_digest_records(records)
    assert selected[0][1]["importance_level"] == "긴급"


def test_build_digest_body_empty_when_no_alert_records():
    assert "없다" in build_digest_body([])


def test_build_digest_body_includes_implications_and_actions():
    body = build_digest_body([(URGENT_ARTICLE, URGENT_INTELLIGENCE)])
    assert "신규 소송 제기" in body
    assert "법무팀 즉시 검토" in body
    assert "[긴급]" in body


def test_build_digest_subject_reflects_count():
    subject_none = build_digest_subject([])
    subject_one = build_digest_subject([(URGENT_ARTICLE, URGENT_INTELLIGENCE)])
    assert "없음" in subject_none
    assert "1건" in subject_one


def test_notifiers_build_digest_message_delegates_to_pipeline():
    subject, body = build_digest_message([(URGENT_ARTICLE, URGENT_INTELLIGENCE)])
    assert "1건" in subject
    assert "신규 소송 제기" in body
