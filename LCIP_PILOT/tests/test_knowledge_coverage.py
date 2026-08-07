"""Round 7 — Knowledge Coverage 8종 지표 검증.

Architect Review Round 7 지시: "Knowledge Quality는 문서 개수 기준이 아니라 Coverage
기준으로 바꾼다." 이 테스트는 8개 도메인(Corporate/Market/Competitor/Government/
Technology/Risk/Opportunity/Investment)이 실제 knowledge/*.md의 올바른 Section을
가리키는지, 그리고 신뢰 가능 여부 판정이 `knowledge_quality.py`와 동일한 결과를 내는지
검증한다.
"""
from __future__ import annotations

import knowledge_coverage as kc
import knowledge_quality


def test_all_8_domains_are_defined():
    assert set(kc.DOMAIN_SECTIONS.keys()) == {
        "corporate", "market", "competitor", "government", "technology",
        "risk", "opportunity", "investment",
    }
    assert set(kc.DOMAIN_LABELS.keys()) == set(kc.DOMAIN_SECTIONS.keys())


def test_every_mapped_section_actually_exists_in_its_file():
    """도메인 매핑에 적힌 (파일, Section 번호)가 실제 파일에 존재하지 않으면 매핑 오류다."""
    for domain, mapping in kc.DOMAIN_SECTIONS.items():
        matched = kc.matched_sections_for_domain(domain)
        assert len(matched) == len(mapping), f"{domain} 도메인에 존재하지 않는 Section이 매핑되어 있다"


def test_coverage_for_domain_returns_percentage():
    for domain in kc.DOMAIN_SECTIONS:
        value = kc.coverage_for_domain(domain)
        assert 0.0 <= value <= 100.0


def test_corporate_coverage_matches_company_section_of_both_profile_docs():
    matched = kc.matched_sections_for_domain("corporate")
    files = {(s.file, s.section_number) for s in matched}
    assert files == {("LX_HAUSYS_COMPANY_DNA.md", 1), ("LX_HOLDINGS_CONTEXT.md", 1)}


def test_investment_coverage_reflects_strategy_playbook_being_draft():
    """STRATEGY_PLAYBOOK.md는 Round 7까지 미착수(confidence: draft)라 Investment Coverage가
    100%가 아니어야 한다 — 회귀 시 이 값이 fabricated 100%로 잘못 올라가지 않았는지 감시."""
    assert kc.coverage_for_domain("investment") < 100.0


def test_is_reliable_matches_knowledge_quality_semantics_for_na_layer():
    """N/A 계층은 knowledge_quality.py와 동일하게 무조건 신뢰 가능해야 한다."""
    sections = kc._sections_for_file("LX_HOLDINGS_CONTEXT.md")
    na_section = next(s for s in sections if s.section_number == 3)  # Product — N/A
    assert kc._is_reliable(na_section) is True


def test_all_coverage_returns_all_8_domains_with_percentages():
    coverage = kc.all_coverage()
    assert set(coverage.keys()) == set(kc.DOMAIN_SECTIONS.keys())
    for value in coverage.values():
        assert 0.0 <= value <= 100.0


def test_unknown_domain_raises():
    import pytest

    with pytest.raises(ValueError):
        kc.coverage_for_domain("no_such_domain")
