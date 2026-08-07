"""Company Intelligence Score — Architect Review Round 8.

Quick Company Scan 결과 하나를 0~100점으로 요약한다. 7개 하위 점수(전부 0~100)를
단순 평균한다 — Pilot 단계에서는 항목별 가중치를 다르게 줄 근거가 없어 동일 가중치를
쓴다. 각 하위 점수는 **완성도** 지표다("이 항목에 실제 내용이 채워져 있는가") —
"내용이 사실인지/정확한지"는 판정하지 않는다. Mock 응답이든 실제 Claude 응답이든
필드가 비어 있지 않으면 동일하게 "채워짐"으로 센다. 정확성 판정은 Pilot이 자동화할
수 없는 영역이다(Round 7 Quality Gate의 Reasoning Quality가 이미 밝힌 한계와 동일).

- **Business Understanding**: company_overview/business_structure/product_portfolio/
  manufacturing/value_chain/customer 6개 필드 중 채워진 비율.
- **Market Position**: competitor/comparable_companies/growth_strategy 3개.
- **Financial Visibility**: financial_snapshot/investment_multiple/capital_market/
  estimated_valuation 4개.
- **Strategic Importance**: lx_strategic_fit/synergy_analysis 2개.
- **Risk Visibility**: risk_assessment/government_exposure 2개.
- **Source Reliability**: 이번 스캔에 실제로 선택된 Source들의
  `source_priority.score_for_source_type()`(1~5점) 평균을 100점 만점으로 환산.
- **Knowledge Coverage**: 이 회사의 Knowledge Base 커버리지 — `knowledge_engine.
  search_by_company()`로 얻은 Section 중 신뢰 가능한 비율. Knowledge 파일 자체가 없는
  회사(LX Hausys 외 대부분)는 정직하게 0점이다 — 지어내지 않는다.
"""
from __future__ import annotations

from dataclasses import dataclass

from knowledge_engine import search_by_company
from source_priority import score_for_source_type

_UNSET_MARKERS = {"", "todo: source required", "미확인"}


def _filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _fraction_filled(report: dict, fields: list[str]) -> float:
    if not fields:
        return 0.0
    filled = sum(1 for f in fields if _filled(report.get(f)))
    return (filled / len(fields)) * 100


def _source_reliability_score(sources: list[dict]) -> float:
    if not sources:
        return 0.0
    scores = [score_for_source_type(s.get("source_type", "")) for s in sources]
    return (sum(scores) / len(scores) / 5) * 100


def _section_is_reliable(section) -> bool:
    confidence = section.confidence.strip()
    reference_url = section.reference_url.strip().lower()
    if confidence.upper() == "N/A":
        return True
    return confidence.lower() not in ("", "draft") and reference_url not in _UNSET_MARKERS


def _knowledge_coverage_score(company_id: str | None) -> float:
    if not company_id:
        return 0.0
    sections = search_by_company(company_id)
    if not sections:
        return 0.0
    reliable = sum(1 for s in sections if _section_is_reliable(s))
    return (reliable / len(sections)) * 100


@dataclass(frozen=True)
class CompanyIntelligenceScore:
    business_understanding: float
    market_position: float
    financial_visibility: float
    strategic_importance: float
    risk_visibility: float
    source_reliability: float
    knowledge_coverage: float

    @property
    def overall(self) -> float:
        values = (
            self.business_understanding, self.market_position, self.financial_visibility,
            self.strategic_importance, self.risk_visibility, self.source_reliability,
            self.knowledge_coverage,
        )
        return sum(values) / len(values)

    def as_dict(self) -> dict:
        return {
            "business_understanding": round(self.business_understanding, 1),
            "market_position": round(self.market_position, 1),
            "financial_visibility": round(self.financial_visibility, 1),
            "strategic_importance": round(self.strategic_importance, 1),
            "risk_visibility": round(self.risk_visibility, 1),
            "source_reliability": round(self.source_reliability, 1),
            "knowledge_coverage": round(self.knowledge_coverage, 1),
            "overall": round(self.overall, 1),
        }


def compute_score(
    company_id: str | None, quick_report: dict, sources: list[dict]
) -> CompanyIntelligenceScore:
    return CompanyIntelligenceScore(
        business_understanding=_fraction_filled(
            quick_report,
            ["company_overview", "business_structure", "product_portfolio",
             "manufacturing", "value_chain", "customer"],
        ),
        market_position=_fraction_filled(
            quick_report, ["competitor", "comparable_companies", "growth_strategy"]
        ),
        financial_visibility=_fraction_filled(
            quick_report,
            ["financial_snapshot", "investment_multiple", "capital_market", "estimated_valuation"],
        ),
        strategic_importance=_fraction_filled(
            quick_report, ["lx_strategic_fit", "synergy_analysis"]
        ),
        risk_visibility=_fraction_filled(
            quick_report, ["risk_assessment", "government_exposure"]
        ),
        source_reliability=_source_reliability_score(sources),
        knowledge_coverage=_knowledge_coverage_score(company_id),
    )
