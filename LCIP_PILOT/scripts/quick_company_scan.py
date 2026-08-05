"""Quick Company Scan — Pilot의 첫 번째 실제 서비스 (Architect Review Round 5).

파이프라인: 입력(회사명/Ticker/DART 회사명) → 자동 Source 선택 → Company Intelligence
생성(Provider) → Quick Report 생성(스키마 검증) → Investment Review 입력 변환.

`config/company_registry.yaml`에 등록되지 않은 회사는 **임의로 지어내지 않고** "미등록"으로
정직하게 처리한다(CLAUDE.md 절대 원칙) — MockProvider/ClaudeProvider 모두 등록 여부와
무관하게 호출은 가능하지만, 등록되지 않은 회사는 `resolved=False`로 표시되어 호출자가
그 사실을 알 수 있다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date

from _common import load_yaml, project_root
from jsonschema import validate as jsonschema_validate
from providers.base import AIProvider, ProviderResult

SCHEMAS_DIR = project_root() / "schemas"


@dataclass(frozen=True)
class CompanyIdentifier:
    company_id: str | None
    display_name: str
    query: str
    ticker: str | None
    dart_name: str | None
    country: str | None
    resolved: bool
    # Round 6 TASK-K02: config/company_registry.yaml에 추가된 필드. 미등록 회사이거나
    # 구버전 레지스트리 항목에는 채워지지 않을 수 있어 전부 기본값 None/빈 값을 둔다.
    industry: str | None = None
    products: list[str] = field(default_factory=list)
    value_chain: str | None = None
    official_website: str | None = None
    primary_disclosure_source: str | None = None


def load_company_registry() -> list[dict]:
    return load_yaml("config/company_registry.yaml")["companies"]


def resolve_company_input(query: str, registry: list[dict] | None = None) -> CompanyIdentifier:
    """회사명/Ticker/DART 회사명 입력을 `config/company_registry.yaml` 기준으로 정규화한다.

    레지스트리에 없으면 임의로 새 회사 정보를 만들어내지 않고 `resolved=False`로 반환한다.
    """
    registry = registry if registry is not None else load_company_registry()
    normalized = query.strip().lower()

    for entry in registry:
        aliases = [a.lower() for a in entry.get("aliases", [])]
        ticker = (entry.get("ticker") or "").lower()
        dart_name = (entry.get("dart_name") or "").lower()
        if normalized in aliases or normalized == entry["company_id"].lower() or (
            ticker and normalized == ticker
        ) or (dart_name and normalized == dart_name):
            return CompanyIdentifier(
                company_id=entry["company_id"],
                display_name=entry["display_name"],
                query=query,
                ticker=entry.get("ticker"),
                dart_name=entry.get("dart_name"),
                country=entry.get("country"),
                resolved=True,
                industry=entry.get("industry"),
                products=list(entry.get("products") or []),
                value_chain=entry.get("value_chain"),
                official_website=entry.get("official_website"),
                primary_disclosure_source=entry.get("primary_disclosure_source"),
            )

    return CompanyIdentifier(
        company_id=None,
        display_name=query,
        query=query,
        ticker=None,
        dart_name=None,
        country=None,
        resolved=False,
    )


def select_sources_for_company(
    company: CompanyIdentifier, sources_config: list[dict] | None = None
) -> list[dict]:
    """회사의 국가/DART 등록 여부에 따라 조회할 Source를 자동으로 고른다.

    - Google News RSS(영문, SRC-0001)는 글로벌 커버리지를 위해 항상 포함한다.
    - 한국 회사면 Google News RSS(한글, SRC-0002)를 추가한다.
    - DART 회사명이 있는 한국 회사면 DART(SRC-0004, `active: false`라도 포함 — 실제 조회
      가능 여부는 `active` 필드로 호출자가 판단한다)를 추가한다.
    """
    sources_config = (
        sources_config if sources_config is not None else load_yaml("config/sources.yaml")["sources"]
    )
    by_id = {s["source_id"]: s for s in sources_config}
    selected: list[dict] = []

    if "SRC-0001" in by_id:
        selected.append(by_id["SRC-0001"])
    if company.country == "KR" and "SRC-0002" in by_id:
        selected.append(by_id["SRC-0002"])
    if company.dart_name and company.country == "KR" and "SRC-0004" in by_id:
        selected.append(by_id["SRC-0004"])

    return selected


def generate_company_intelligence(
    provider: AIProvider, company: CompanyIdentifier, sources: list[dict]
) -> ProviderResult:
    """Provider(Mock/Claude)를 호출해 Company Intelligence(quick_company_scan_output)를
    생성한다."""
    company_payload = {
        "display_name": company.display_name,
        "query": company.query,
        "company_id": company.company_id,
    }
    return provider.quick_company_scan(company_payload, sources)


def validate_quick_report(report: dict) -> None:
    schema = json.loads((SCHEMAS_DIR / "quick_company_scan.schema.json").read_text(encoding="utf-8"))
    jsonschema_validate(instance=report, schema=schema)


def build_quick_report(company: CompanyIdentifier, provider_result: ProviderResult) -> dict:
    """Provider 출력을 Quick Report(schemas/quick_company_scan.schema.json)로 확정한다.

    target_company/scan_date를 Provider가 채우지 않았으면 여기서 보정한다(Normalize의
    article_id 발급과 동일한 역할 — 산출물의 정체성은 Pipeline이 보증한다).
    """
    report = dict(provider_result.parsed_json)
    report.setdefault("target_company", company.display_name)
    report.setdefault("scan_date", date.today().isoformat())
    validate_quick_report(report)
    return report


def build_investment_review_input(quick_report: dict) -> dict:
    """Quick Report에서 Investment Review Engine(`scripts/investment_review.py`)이
    필요로 하는 부분만 골라 정규화한다. `risk_assessment`/`synergy_analysis`는 Advanced
    Section(선택) 필드라 Quick Report에 없을 수 있다 — 없으면 빈 배열로 정직하게 둔다
    (임의로 만들어내지 않는다)."""
    return {
        "target_company": quick_report["target_company"],
        "financial_snapshot": quick_report.get("financial_snapshot", []),
        "competitor": quick_report.get("competitor", []),
        "lx_strategic_fit": quick_report.get("lx_strategic_fit", ""),
        "comparable_companies": quick_report.get("comparable_companies", []),
        "investment_multiple": quick_report.get("investment_multiple"),
        "risk_assessment": quick_report.get("risk_assessment", []),
        "synergy_analysis": quick_report.get("synergy_analysis", []),
        "unknowns": list(quick_report.get("unknowns", [])),
        "confidence": quick_report.get("confidence", "low"),
    }
