"""Round 7 — Knowledge Coverage 8종 지표 검증.

Architect Review Round 7 지시: "Knowledge Quality는 문서 개수 기준이 아니라 Coverage
기준으로 바꾼다." 이 테스트는 8개 도메인(Corporate/Market/Competitor/Government/
Technology/Risk/Opportunity/Investment)이 실제 knowledge/*.md의 올바른 Section을
가리키는지, 그리고 신뢰 가능 여부 판정이 `knowledge_quality.py`와 동일한 결과를 내는지
검증한다.
"""
from __future__ import annotations

import pytest

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


# --- Round 8: Company/Country/Industry Coverage ---


def test_company_coverage_returns_percentage_within_range():
    assert 0.0 <= kc.company_coverage() <= 100.0


def test_company_coverage_reflects_only_lx_hausys_has_knowledge_today():
    """Company Registry는 30개사지만 COMPANY_KNOWLEDGE_FILES에는 LX_HAUSYS만 매핑되어
    있다 — 회귀 시 이 값이 부풀려진 100%로 잘못 올라가지 않았는지 감시(정직성 원칙)."""
    from registries.manager import RegistryManager

    total_companies = len(RegistryManager().get_registry("company").list_entries())
    expected = (1 / total_companies) * 100
    assert kc.company_coverage() == pytest.approx(expected)


def test_country_coverage_returns_percentage_within_range():
    assert 0.0 <= kc.country_coverage() <= 100.0


def test_country_coverage_excludes_inactive_multi_placeholder_sources():
    """SRC-0010/0011(country: multi)은 둘 다 active: false 카테고리 placeholder다 —
    이걸 '모든 국가 커버'로 세면 정직성 원칙 위반이라 실제로는 KR/US만 커버된다."""
    from registries.manager import RegistryManager

    companies = RegistryManager().get_registry("company").list_entries()
    distinct_countries = {c["country"] for c in companies if c.get("country")}
    covered = {"KR", "US"} & distinct_countries
    expected = (len(covered) / len(distinct_countries)) * 100
    assert kc.country_coverage() == pytest.approx(expected)


def test_industry_coverage_returns_percentage_within_range():
    assert 0.0 <= kc.industry_coverage() <= 100.0


def test_industry_coverage_uses_exact_string_match_not_keyword_similarity():
    """industry는 자유 텍스트라 지금은 LX_HAUSYS의 정확한 industry 문자열 1개만
    커버된다 — 키워드 유사 매칭으로 뭉뚱그려 값이 부풀려지지 않았는지 감시."""
    from registries.manager import RegistryManager

    companies = RegistryManager().get_registry("company").list_entries()
    distinct_industries = {c["industry"] for c in companies if c.get("industry")}
    expected = (1 / len(distinct_industries)) * 100
    assert kc.industry_coverage() == pytest.approx(expected)


def test_registry_coverage_returns_all_3_metrics():
    coverage = kc.registry_coverage()
    assert set(coverage.keys()) == {"company", "country", "industry"}
    for value in coverage.values():
        assert 0.0 <= value <= 100.0
