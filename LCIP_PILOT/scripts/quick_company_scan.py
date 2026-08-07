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
from html import escape

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


def retrieve_knowledge_for_company(company: CompanyIdentifier) -> str:
    """Architect Review Round 8 — Quick Company Scan 파이프라인에 Knowledge Retrieval
    단계를 추가한다(Input -> Company Registry -> **Knowledge Retrieval** -> Source
    Selection -> ...). `knowledge_engine.search_by_company()`를 재사용한다 — 새 검색
    로직을 만들지 않는다. Knowledge 파일이 등록되지 않은 회사(현재 LX Hausys 외 대부분)는
    빈 문자열을 정직하게 반환한다(임의로 지어내지 않는다).
    """
    if not company.company_id:
        return ""
    from knowledge_engine import search_by_company

    sections = search_by_company(company.company_id)
    if not sections:
        return ""
    return "\n\n".join(f"[{s.file} §{s.section_number} {s.section_title}]\n{s.content}" for s in sections)


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
    provider: AIProvider,
    company: CompanyIdentifier,
    sources: list[dict],
    knowledge_excerpt: str = "",
) -> ProviderResult:
    """Provider(Mock/Claude)를 호출해 Company Intelligence(quick_company_scan_output)를
    생성한다. `knowledge_excerpt`는 `retrieve_knowledge_for_company()`의 산출물이다."""
    company_payload = {
        "display_name": company.display_name,
        "query": company.query,
        "company_id": company.company_id,
    }
    return provider.quick_company_scan(company_payload, sources, knowledge_excerpt)


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


def _bullets(items: list[str]) -> str:
    """`quick_report`의 리스트 필드를 사람이 읽기 좋게 렌더링한다. Provider가 항목 하나당
    긴 문단을 통째로 넣는 경우(Knowledge Base 발췌, mock 안내문 등)가 흔해서, 1건뿐이면
    그 문단을 그대로 보여주고(불필요한 "- -" 중첩 방지), 여러 건이면 각각 "- "로 나열한다."""
    if not items:
        return "(확인된 내용 없음)"
    if len(items) == 1:
        return items[0]
    return "\n".join(f"- {item}" for item in items)


def _render_quick_scan_markdown(quick_report: dict, investment_review: dict, intelligence_score: dict) -> str:
    """Architect Review Round 9 — "실제 전략팀 직원이 바로 사용할 수 있는가?"에 대한
    답으로, Quick Report의 Core 7 필드 전체(이전에는 company_overview만 보여줬다)와
    Investment Review의 Comparable Valuation·추천 사유까지 한 페이지에 담는다. 새 필드나
    새 계산 로직은 추가하지 않는다 — 이미 있는 값을 빠짐없이 보여주기만 한다."""
    rec = investment_review["recommendation"]
    peer_avg = investment_review["peer_average"]
    comparable = investment_review.get("comparable", [])

    lines = [
        f"# Quick Company Scan — {quick_report['target_company']}",
        "",
        f"- Scan Date: {quick_report['scan_date']}",
        f"- Confidence: {quick_report['confidence']}",
        f"- Company Intelligence Score: **{intelligence_score['overall']}/100**",
        "",
        "## Company Intelligence Score 세부",
        *[f"- {k}: {v}" for k, v in intelligence_score.items() if k != "overall"],
        "",
        "## Company Overview",
        quick_report.get("company_overview", "(확인된 내용 없음)"),
        "",
        "## Business Structure",
        _bullets(quick_report.get("business_structure", [])),
        "",
        "## Product Portfolio",
        _bullets(quick_report.get("product_portfolio", [])),
        "",
        "## Financial Snapshot",
        _bullets(quick_report.get("financial_snapshot", [])),
        "",
        "## Competitor",
        _bullets(quick_report.get("competitor", [])),
        "",
        "## LX Strategic Fit",
        quick_report.get("lx_strategic_fit", "(확인된 내용 없음)"),
        "",
        "## Investment Review (Comparable 기반)",
        f"- Recommendation Signal: **{rec['signal']}**",
        f"- Rationale: {rec.get('rationale', '')}",
        f"- Deal Killer Found: {investment_review['deal_killer']['found']}",
    ]
    if investment_review["deal_killer"]["found"]:
        lines.append(f"- Deal Killer Reasons: {'; '.join(investment_review['deal_killer']['reasons'])}")
    lines += [
        f"- Comparable Peer 수: {peer_avg['peer_count']}건"
        + ("(회사명은 실제 기업 — 배수는 확인된 값만 표시, 미확인은 '-')" if comparable else ""),
    ]
    if comparable:
        lines.append("")
        lines.append("| Peer | EV/EBITDA | PER | PBR |")
        lines.append("|---|---|---|---|")
        for peer in comparable:
            ev_ebitda = peer["ev_ebitda"] if peer["ev_ebitda"] is not None else "-"
            per = peer["per"] if peer["per"] is not None else "-"
            pbr = peer["pbr"] if peer["pbr"] is not None else "-"
            lines.append(f"| {peer['peer_name']} | {ev_ebitda} | {per} | {pbr} |")
    lines += [
        "",
        "## 확인되지 않은 사항 (Unknowns)",
        _bullets(quick_report.get("unknowns", [])),
        "",
        "## 참고 출처 (Reference Sources)",
        _bullets(quick_report.get("reference_sources", [])),
        "",
        "> Confidence가 'low'인 항목은 Mock/미확인 상태다 — 실제 Claude 연동(RC2) 전까지는",
        "> 초안(draft) 참고용으로만 사용하고, 전략팀 검토자료에는 출처를 재확인한 뒤 반영한다.",
    ]
    return "\n".join(lines)


def build_executive_report_html(
    quick_report: dict, investment_review: dict, intelligence_score: dict
) -> str:
    """Architect Review Round 11 Priority 3 — Quick Company Scan 결과를 임원 보고용
    1~2페이지 요약본으로 자동 생성한다. Pilot은 HTML만 지원한다(PDF는 구현하지 않는다).

    `_render_quick_scan_markdown()`(상세본, Core 7 필드 전부)과 달리 이 요약본은 임원이
    3분 안에 판단할 수 있는 핵심(점수·추천신호·근거·Top 3 리스크·Peer 수)만 추린다.
    새 CSS 프레임워크를 만들지 않고 `dashboard/styles.css`와 같은 톤(흰 배경·남색
    accent·얇은 구분선)을 이 파일 안에 직접 인라인한다 — Dashboard 파일에 대한 의존성
    없이 단독으로 열람 가능해야 하기 때문이다(이메일 첨부·인쇄 용도)."""
    rec = investment_review["recommendation"]
    peer_avg = investment_review["peer_average"]
    top_unknowns = quick_report.get("unknowns", [])[:3]

    unknowns_html = (
        "".join(f"<li>{escape(u)}</li>" for u in top_unknowns)
        if top_unknowns else "<li>확인된 미확인 사항 없음</li>"
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>{escape(quick_report['target_company'])} — Executive Report</title>
<style>
  body {{ font-family: Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
          color: #1c1c1c; max-width: 720px; margin: 32px auto; padding: 0 20px;
          line-height: 1.6; word-break: keep-all; }}
  h1 {{ font-size: 1.375rem; border-bottom: 1px solid #e2e4e8; padding-bottom: 12px; margin-bottom: 4px; }}
  .meta {{ color: #5f6368; font-size: 0.875rem; margin-bottom: 24px; }}
  .score {{ border-left: 3px solid #0b3d91; padding: 12px 16px; margin-bottom: 20px; background: #fff; }}
  .score .num {{ font-size: 2rem; font-weight: 700; color: #0b3d91; }}
  h2 {{ font-size: 1rem; border-bottom: 1px solid #e2e4e8; padding-bottom: 6px; margin: 24px 0 8px; }}
  ul {{ margin: 0; padding-left: 20px; }}
  .footer {{ color: #5f6368; font-size: 0.75rem; border-top: 1px solid #e2e4e8;
             padding-top: 12px; margin-top: 28px; }}
  @media print {{ body {{ margin: 0; }} }}
</style>
</head>
<body>
  <h1>{escape(quick_report['target_company'])} — Executive Report</h1>
  <div class="meta">Scan Date: {escape(quick_report['scan_date'])} · Confidence: {escape(quick_report['confidence'])}
    · LCIP Pilot · LX홀딩스 전략팀 참고용</div>

  <div class="score">
    <div class="num">{intelligence_score['overall']}/100</div>
    <div>Company Intelligence Score</div>
  </div>

  <h2>투자 시그널</h2>
  <p><strong>{escape(rec['signal'])}</strong> — {escape(rec.get('rationale', ''))}</p>
  <p>Deal Killer 발견: {"예" if investment_review['deal_killer']['found'] else "아니오"}
    · Comparable Peer: {peer_avg['peer_count']}건</p>

  <h2>회사 개요</h2>
  <p>{escape(quick_report.get('company_overview', '(확인된 내용 없음)'))}</p>

  <h2>LX Strategic Fit</h2>
  <p>{escape(quick_report.get('lx_strategic_fit', '(확인된 내용 없음)'))}</p>

  <h2>주요 확인 필요 사항 (Top 3 Unknowns)</h2>
  <ul>{unknowns_html}</ul>

  <div class="footer">
    본 요약본은 공개정보 기반 Pilot 산출물이며, Confidence가 'low'인 항목은 초안 참고용이다.
    상세 근거는 같은 폴더의 Markdown 전체 보고서를 참고한다. Mock/dry-run 결과가 섞여 있을
    수 있다.
  </div>
</body>
</html>
"""


def export_quick_scan_report(
    company: CompanyIdentifier,
    quick_report: dict,
    investment_review: dict,
    intelligence_score: dict,
    out_dir=None,
) -> dict:
    """Architect Review Round 8 — 파이프라인의 마지막 단계(Export). Quick Report +
    Investment Review + Company Intelligence Score를 하나로 묶어 JSON(기계 판독용)과
    Markdown(사람이 읽는 상세 요약) 두 파일로 내보낸다. `output/`(gitignore 대상)에 쓰므로
    Git에는 포함되지 않는다 — 시연 시 그 자리에서 생성해 보여주는 산출물이다.

    Round 11 Priority 3("Quick Company Scan 결과를 임원 보고용 1~2페이지 요약본으로
    자동 생성한다. HTML 또는 Markdown 둘 중 하나만 지원한다")에 따라, 같은 Export
    단계에서 HTML Executive Report(`build_executive_report_html()`)도 세 번째
    파일로 함께 내보낸다 — 새 파이프라인 단계를 추가하지 않고 기존 Export 단계의
    산출물 종류만 늘린다.
    """
    out_dir = out_dir if out_dir is not None else project_root() / "output" / "quick_company_scan_exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = (company.company_id or company.query).strip().replace(" ", "_").upper()
    combined = {
        "company_id": company.company_id,
        "target_company": quick_report["target_company"],
        "scan_date": quick_report["scan_date"],
        "quick_report": quick_report,
        "investment_review": investment_review,
        "company_intelligence_score": intelligence_score,
    }

    json_path = out_dir / f"{safe_name}.json"
    json_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = out_dir / f"{safe_name}.md"
    md_path.write_text(_render_quick_scan_markdown(quick_report, investment_review, intelligence_score), encoding="utf-8")

    executive_report_path = out_dir / f"{safe_name}_executive_report.html"
    executive_report_path.write_text(
        build_executive_report_html(quick_report, investment_review, intelligence_score), encoding="utf-8"
    )

    return {"json_path": json_path, "md_path": md_path, "executive_report_path": executive_report_path}


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
