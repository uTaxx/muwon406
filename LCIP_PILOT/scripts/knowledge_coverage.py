#!/usr/bin/env python3
"""Knowledge Coverage — Architect Review Round 7.

Round 6까지의 Knowledge Quality Score(95.8%)는 "12계층 Company Profile 문서가 얼마나
채워졌는가"(문서 단위 완성도)를 측정했다. Round 7 지시: "Knowledge Quality는 문서 개수
기준이 아니라 Coverage 기준으로 바꾼다" — 이 모듈은 knowledge/*.md 전체 중 실제 회사
사실을 담은 "운영 데이터" 문서(`pipeline/knowledge_retrieve.py:COMPANY_KNOWLEDGE_FILES`와
동일 목록 — 새 목록을 만들지 않는다)를 8개 지식 도메인(Corporate/Market/Competitor/
Government/Technology/Risk/Opportunity/Investment)으로 나눠, 각 도메인에 실제로 대응하는
Section이 신뢰 가능한 상태인지를 %로 측정한다.

Framework/Policy류 거버넌스 문서(ANALYSIS_FRAMEWORK.md, MISSION_FRAMEWORK.md 등)는
"회사 사실"이 아니라 "운영 규칙"이라 Coverage 채점 대상이 아니다 — 이미
`COMPANY_KNOWLEDGE_FILES`에 포함되지 않으므로 자동으로 제외된다.

도메인 -> Section 매핑은 키워드 유사 매칭이 아니라 (파일, Section 번호) 명시적 목록이다.
"Manufacturing"이라는 단어가 `LX_HAUSYS_COMPANY_DNA.md` §4(기술/생산거점 관점)와
`LX_HAUSYS_VALUE_CHAIN.md` §2(시장/유통 관점)에 동시에 등장하는 것처럼, 같은 단어가
다른 도메인을 가리키는 경우가 있어 키워드만으로는 정확히 분리할 수 없기 때문이다.

신뢰 가능 여부 판정은 `knowledge_quality.py`가 이미 쓰는 규칙(Confidence != draft,
Reference URL 존재, Last Verified 신선도, N/A는 무조건 신뢰 가능)을 그대로 재사용한다 —
Round 6이 지적한 "새 판정 로직 중복 생성"을 반복하지 않는다.
"""
from __future__ import annotations

import argparse
from datetime import date

import knowledge_quality
from knowledge_engine import KnowledgeSection, parse_knowledge_sections

# 도메인 -> [(파일명, Section 번호), ...]. 순서는 보고 시 가독성을 위한 것일 뿐 채점에는
# 영향을 주지 않는다.
DOMAIN_SECTIONS: dict[str, list[tuple[str, int]]] = {
    "corporate": [
        ("LX_HAUSYS_COMPANY_DNA.md", 1),   # Company
        ("LX_HOLDINGS_CONTEXT.md", 1),
    ],
    "market": [
        ("LX_HAUSYS_COMPANY_DNA.md", 2),   # Business
        ("LX_HAUSYS_COMPANY_DNA.md", 6),   # Customer
        ("LX_HOLDINGS_CONTEXT.md", 2),
        ("LX_HOLDINGS_CONTEXT.md", 6),
        ("LX_HAUSYS_VALUE_CHAIN.md", 1),   # 원재료 조달(Upstream)
        ("LX_HAUSYS_VALUE_CHAIN.md", 3),   # 유통·판매(Distribution)
        ("LX_HAUSYS_VALUE_CHAIN.md", 4),   # 고객·최종 사용처(Downstream)
    ],
    "competitor": [
        ("LX_HAUSYS_COMPANY_DNA.md", 7),   # Competitor
        ("LX_HOLDINGS_CONTEXT.md", 7),
    ],
    "government": [
        ("LX_HAUSYS_COMPANY_DNA.md", 9),   # Government
        ("LX_HOLDINGS_CONTEXT.md", 9),
    ],
    "technology": [
        ("LX_HAUSYS_COMPANY_DNA.md", 3),   # Product
        ("LX_HAUSYS_COMPANY_DNA.md", 4),   # Manufacturing
        ("LX_HAUSYS_COMPANY_DNA.md", 8),   # Raw Material
        ("LX_HOLDINGS_CONTEXT.md", 3),
        ("LX_HOLDINGS_CONTEXT.md", 4),
        ("LX_HOLDINGS_CONTEXT.md", 8),
        ("LX_HAUSYS_VALUE_CHAIN.md", 2),   # 생산(Manufacturing)
    ],
    "risk": [
        ("LX_HAUSYS_COMPANY_DNA.md", 10),  # Risk
        ("LX_HOLDINGS_CONTEXT.md", 10),
        ("GROUP_RISK_MAP.md", 2),          # 실제 리스크 신호(카테고리 정의/갱신 규칙 제외)
        ("LX_HAUSYS_VALUE_CHAIN.md", 5),   # Value Chain 상 리스크 전이 경로
    ],
    "opportunity": [
        ("LX_HAUSYS_COMPANY_DNA.md", 11),  # Opportunity
        ("LX_HOLDINGS_CONTEXT.md", 11),
        ("GROUP_OPPORTUNITY_MAP.md", 2),   # 실제 기회 신호(카테고리 정의/갱신 규칙 제외)
    ],
    "investment": [
        ("LX_HAUSYS_COMPANY_DNA.md", 12),  # Investment Point
        ("LX_HOLDINGS_CONTEXT.md", 12),
        ("STRATEGY_PLAYBOOK.md", 1),
        ("STRATEGY_PLAYBOOK.md", 2),
    ],
}

DOMAIN_LABELS: dict[str, str] = {
    "corporate": "Corporate Coverage",
    "market": "Market Coverage",
    "competitor": "Competitor Coverage",
    "government": "Government Coverage",
    "technology": "Technology Coverage",
    "risk": "Risk Coverage",
    "opportunity": "Opportunity Coverage",
    "investment": "Investment Coverage",
}

_FILE_CACHE: dict[str, list[KnowledgeSection]] = {}


def _sections_for_file(filename: str) -> list[KnowledgeSection]:
    if filename not in _FILE_CACHE:
        _FILE_CACHE[filename] = parse_knowledge_sections(filename)
    return _FILE_CACHE[filename]


def _is_reliable(section: KnowledgeSection, today: date | None = None) -> bool:
    """knowledge_quality.py의 12계층 채점 규칙을 그대로 재사용한다(로직 중복 방지)."""
    today = today or date.today()
    confidence, reference_url = section.confidence, section.reference_url
    if knowledge_quality._is_na(confidence, reference_url):
        return True
    if not confidence and not reference_url and not section.last_verified:
        return False
    return (
        not knowledge_quality._is_unset(confidence)
        and confidence.strip().lower() != "draft"
        and not knowledge_quality._is_unset(reference_url)
        and knowledge_quality._is_fresh(
            section.last_verified, today, knowledge_quality.FRESHNESS_DAYS_COMPANY_PROFILE
        )
    )


def matched_sections_for_domain(domain: str) -> list[KnowledgeSection]:
    if domain not in DOMAIN_SECTIONS:
        raise ValueError(f"알 수 없는 Coverage 도메인: '{domain}' — {list(DOMAIN_SECTIONS)} 중 하나여야 한다")
    matched = []
    for filename, section_number in DOMAIN_SECTIONS[domain]:
        section = next(
            (s for s in _sections_for_file(filename) if s.section_number == section_number), None
        )
        if section is not None:
            matched.append(section)
    return matched


def coverage_for_domain(domain: str) -> float:
    matched = matched_sections_for_domain(domain)
    if not matched:
        return 0.0
    reliable = sum(1 for s in matched if _is_reliable(s))
    return (reliable / len(matched)) * 100


def all_coverage() -> dict[str, float]:
    return {domain: coverage_for_domain(domain) for domain in DOMAIN_SECTIONS}


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Knowledge Coverage (Round 7)")
    parser.add_argument("--verbose", action="store_true", help="도메인별 매칭 Section 상세 출력")
    args = parser.parse_args()

    print("=== Knowledge Coverage (Architect Review Round 7) ===")
    coverage = all_coverage()
    for domain, label in DOMAIN_LABELS.items():
        print(f"{label:22s}: {coverage[domain]:5.1f}%")
        if args.verbose:
            for section in matched_sections_for_domain(domain):
                status = "OK" if _is_reliable(section) else "미확정"
                print(f"    - {section.file} §{section.section_number} [{status}]")

    overall = sum(coverage.values()) / len(coverage) if coverage else 0.0
    print(f"\n전체 평균: {overall:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
