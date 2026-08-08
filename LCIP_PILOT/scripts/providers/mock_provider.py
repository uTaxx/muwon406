"""MockProvider — 실제 API 호출 없이 결정론적 응답을 반환한다.

Round 4 지시("외부 API 실제 호출은 아직 시작하지 않는다. Mock 기반으로 구조와 테스트를
먼저 완성한다")에 따라, Pipeline/Integration Test는 기본적으로 이 Provider를 사용한다.
"""
from __future__ import annotations

from datetime import date

from .base import AIProvider, ProviderResult, ProviderUsage

# Architect Review Round 9 — "실제 사용 가능한 Pilot": 이전에는 Knowledge Base에 실제
# 사실이 있어도 MockProvider가 이를 버리고 항상 "mock: ... 미확인"만 반환해, LX Hausys처럼
# Round 6에서 실제 리서치를 마친 회사조차 쓸모없는 Report가 나왔다. 실제 Claude 호출은
# 여전히 하지 않되(confidence는 계속 "low"), Knowledge Base에 이미 있는 신뢰 가능한 사실은
# 그대로 노출한다. Core 7 필드 중 Knowledge 16계층 Taxonomy에 대응 Section이 있는 4개
# (company_overview=§1/business_structure=§2/product_portfolio=§3/competitor=§7)만
# 채운다 — financial_snapshot/lx_strategic_fit은 Taxonomy에 신뢰할 만한 대응 Section이
# 없거나(§12 Investment Point는 LX Hausys 자체 기준 "해당 없음") 재무 데이터라 Round 9
# 지시("Pilot에서는 Mock Financial Data 유지")대로 계속 mock 텍스트로 남긴다.
#
# `search_by_company()`(Round 5)는 그 회사에 매핑된 파일 전체(LX Hausys는 7개 파일)를
# 하나로 이어붙인다 — 각 파일이 자기 자신의 §1~16을 갖고 있어(예: LX_HOLDINGS_CONTEXT.md도
# §7 Competitor를 갖는다), 단순히 "Section 번호"로만 찾으면 다른 회사/문서의 §7이 LX
# Hausys의 §7을 덮어쓸 수 있다(knowledge_coverage.py가 도메인 매핑에 (파일, Section 번호)
# 명시적 쌍을 쓰는 것과 동일한 이유). 그래서 여기서는 `knowledge/KNOWLEDGE_POLICY.md` §4가
# 정한 우선순위(CLAUDE.md 8번 항목)의 1순위 문서 — 그 회사의 Company Profile 원본 —
# 하나만 직접 파싱한다.
_KNOWLEDGE_FIELD_SECTIONS = {
    "company_overview": 1,
    "business_structure": 2,
    "product_portfolio": 3,
    "competitor": 7,
}


def _is_usable_section(section) -> bool:
    confidence = section.confidence.strip().lower()
    return confidence not in ("", "draft")


def _real_knowledge_fields(company_id: str | None) -> dict[str, str]:
    if not company_id:
        return {}
    from pipeline.knowledge_retrieve import COMPANY_KNOWLEDGE_FILES

    files = COMPANY_KNOWLEDGE_FILES.get(company_id) or []
    if not files:
        return {}

    from knowledge_engine import parse_knowledge_sections

    primary_profile_file = files[0]  # KNOWLEDGE_POLICY.md §4 우선순위의 1순위 문서
    sections = parse_knowledge_sections(primary_profile_file)
    by_number = {s.section_number: s for s in sections}
    result: dict[str, str] = {}
    for field, section_number in _KNOWLEDGE_FIELD_SECTIONS.items():
        section = by_number.get(section_number)
        if section is not None and section.content.strip() and _is_usable_section(section):
            result[field] = section.content.strip()
    return result


class MockProvider(AIProvider):
    """규칙 기반으로 그럴듯한 응답을 만드는 Mock. 실제 Claude를 호출하지 않는다."""

    def __init__(self):
        self.call_count = 0

    def classify_relevance(self, article: dict, topic: dict) -> ProviderResult:
        self.call_count += 1
        title = (article.get("title_original") or "").lower()
        is_silica_related = any(
            kw in title for kw in ["silic", "실리코시스", "엔지니어드스톤", "quartz", "stone"]
        )
        # mission_category는 스키마상 relevant 여부와 무관하게 minItems=1 필수다 — 관련 없다고
        # 판단해도 이 Topic이 속한 미션 축은 항상 존재하므로(Topic 자체의 mission_category를
        # 그대로 사용) 빈 배열을 반환하지 않는다.
        topic_mission_category = topic.get("mission_category") or ["risk_management"]
        parsed = {
            "relevant": is_silica_related,
            "relevance_score": 0.85 if is_silica_related else 0.1,
            "mission_category": ["risk_management"] if is_silica_related else topic_mission_category,
            "mission_subcategory": ["litigation", "safety"] if is_silica_related else [],
            "intelligence_categories": ["litigation", "product"] if is_silica_related else ["macro"],
            "related_companies": topic.get("related_lx_companies", []) if is_silica_related else [],
            "reason": (
                "제목에 실리코시스/엔지니어드스톤 관련 키워드가 포함됨 (mock 판정)"
                if is_silica_related
                else "제목에 Topic 관련 키워드가 없음 (mock 판정)"
            ),
            "needs_deep_analysis": is_silica_related,
        }
        if not is_silica_related:
            parsed.pop("mission_subcategory")
        return ProviderResult(
            ok=True,
            parsed_json=parsed,
            raw_text=str(parsed),
            usage=ProviderUsage(input_tokens=120, output_tokens=60, model="mock-classifier"),
        )

    def analyze_risk(
        self,
        article: dict,
        lx_context_excerpt: str,
        existing_timeline_excerpt: str,
        group_ai_instructions: str = "",
    ) -> ProviderResult:
        self.call_count += 1
        title = article.get("title_original", "샘플 기사")
        parsed = {
            "facts": [f"원문 제목: {title}"],
            "significance": "중요 — mock 심층분석 (실제 Claude 미연동)",
            "importance_level": "중요",
            "mission_category": ["risk_management"],
            "mission_subcategory": ["litigation"],
            "intelligence_categories": ["litigation", "product"],
            "lx_impact": [] if not lx_context_excerpt else ["LX Hausys Knowledge Base 발췌 근거로 영향 가능성 있음 (mock)"],
            "actions": ["추가 모니터링 필요 (mock 제안)"],
            "confidence": "low",
            "evidence": [article.get("source_url", "https://example.com/mock-source")],
            "unknowns": ["실제 Claude 미연동 상태 — mock 결과이므로 신뢰하지 말 것"],
        }
        return ProviderResult(
            ok=True,
            parsed_json=parsed,
            raw_text=str(parsed),
            usage=ProviderUsage(input_tokens=800, output_tokens=300, model="mock-analyzer"),
        )

    def analyze_policy_impact(
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        self.call_count += 1
        title = article.get("title_original", "샘플 정책 기사")
        parsed = {
            "facts": [f"원문 제목: {title}"],
            "regulatory_stage": "unknown",
            "significance": "중요 — mock 정책 영향 분석 (실제 Claude 미연동)",
            "importance_level": "중요",
            "mission_category": ["risk_management"],
            "mission_subcategory": ["regulatory"],
            "intelligence_categories": ["regulation", "government"],
            "lx_impact": [] if not lx_context_excerpt else ["LX Hausys Knowledge Base 발췌 근거로 규제 영향 가능성 있음 (mock)"],
            "actions": ["규제 단계 추가 모니터링 필요 (mock 제안)"],
            "confidence": "low",
            "evidence": [article.get("source_url", "https://example.com/mock-policy-source")],
            "unknowns": ["실제 Claude 미연동 상태 — mock 결과이므로 신뢰하지 말 것"],
        }
        return ProviderResult(
            ok=True,
            parsed_json=parsed,
            raw_text=str(parsed),
            usage=ProviderUsage(input_tokens=800, output_tokens=300, model="mock-policy-analyzer"),
        )

    def quick_company_scan(
        self, company: dict, sources: list[dict], knowledge_excerpt: str = ""
    ) -> ProviderResult:
        self.call_count += 1
        display_name = company.get("display_name") or company.get("query") or "알 수 없는 회사"
        source_names = [s.get("source_name", "") for s in sources] or ["등록된 Source 없음"]
        real = _real_knowledge_fields(company.get("company_id"))
        parsed = {
            "target_company": display_name,
            "scan_date": date.today().isoformat(),
            "company_overview": real.get(
                "company_overview", f"{display_name}에 대한 공개정보 요약 (mock — 실제 Claude 미연동)"
            ),
            "business_structure": [real["business_structure"]] if "business_structure" in real else [
                "mock: 사업부 구성 정보 미확인"
            ],
            "product_portfolio": [real["product_portfolio"]] if "product_portfolio" in real else [
                "mock: 주요 제품 정보 미확인"
            ],
            "financial_snapshot": ["mock: 공개 재무 스냅샷 미확인"],
            "competitor": [real["competitor"]] if "competitor" in real else ["mock: 경쟁사 정보 미확인"],
            "lx_strategic_fit": "mock: LX 전략적 연관성 미평가 (실제 Claude 미연동)",
            "reference_sources": [s.get("endpoint_url", "https://example.com/mock-source") for s in sources]
            or ["https://example.com/mock-source"],
            "unknowns": [
                "실제 Claude 미연동 상태 — mock 결과이므로 신뢰하지 말 것",
            ]
            + (
                [f"Knowledge Base 근거로 채운 항목: {', '.join(sorted(real))}"]
                if real
                else ["Knowledge Base 발췌 없음(등록된 Knowledge 파일 없는 회사)"]
            )
            + [f"조회된 Source: {', '.join(source_names)}"],
            "confidence": "low",
        }
        return ProviderResult(
            ok=True,
            parsed_json=parsed,
            raw_text=str(parsed),
            usage=ProviderUsage(input_tokens=1500, output_tokens=500, model="mock-quick-scan"),
        )
