"""MockProvider — 실제 API 호출 없이 결정론적 응답을 반환한다.

Round 4 지시("외부 API 실제 호출은 아직 시작하지 않는다. Mock 기반으로 구조와 테스트를
먼저 완성한다")에 따라, Pipeline/Integration Test는 기본적으로 이 Provider를 사용한다.
"""
from __future__ import annotations

from datetime import date

from .base import AIProvider, ProviderResult, ProviderUsage


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
        self, article: dict, lx_context_excerpt: str, existing_timeline_excerpt: str
    ) -> ProviderResult:
        self.call_count += 1
        title = article.get("title_original", "샘플 기사")
        parsed = {
            "facts": [f"원문 제목: {title}"],
            "significance": "중요 — mock 심층분석 (실제 Claude 미연동)",
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
        parsed = {
            "target_company": display_name,
            "scan_date": date.today().isoformat(),
            "company_overview": f"{display_name}에 대한 공개정보 요약 (mock — 실제 Claude 미연동)",
            "business_structure": ["mock: 사업부 구성 정보 미확인"],
            "product_portfolio": ["mock: 주요 제품 정보 미확인"],
            "financial_snapshot": ["mock: 공개 재무 스냅샷 미확인"],
            "competitor": ["mock: 경쟁사 정보 미확인"],
            "lx_strategic_fit": "mock: LX 전략적 연관성 미평가 (실제 Claude 미연동)",
            "reference_sources": [s.get("endpoint_url", "https://example.com/mock-source") for s in sources]
            or ["https://example.com/mock-source"],
            "unknowns": [
                "실제 Claude 미연동 상태 — mock 결과이므로 신뢰하지 말 것",
                f"조회된 Source: {', '.join(source_names)}",
            ]
            + ([] if knowledge_excerpt else ["Knowledge Base 발췌 없음(등록된 Knowledge 파일 없는 회사)"]),
            "confidence": "low",
        }
        return ProviderResult(
            ok=True,
            parsed_json=parsed,
            raw_text=str(parsed),
            usage=ProviderUsage(input_tokens=1500, output_tokens=500, model="mock-quick-scan"),
        )
