"""Investment Review Engine (Architect Review Round 5).

Quick Company Scan의 `build_investment_review_input()` 출력 + Comparable Peer 목록을 받아
Comparable(비교기업 배수) 기반 Valuation과 스크리닝 신호를 만든다.

절대 원칙(`knowledge/INVESTMENT_FRAMEWORK.md`와 동일):
- 최종 투자판단을 내리지 않는다 — "검토 대상 스크리닝 신호"까지만 제공한다.
- DCF는 사용하지 않는다 — Pilot 범위는 Comparable 기반만 다루며, DCF는 Enterprise
  Backlog다(Architect Review Round 5 명시).
- 확인되지 않은 재무 수치를 임의로 추정하지 않는다 — Peer 데이터가 없으면
  `estimated_valuation`은 null.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from _common import project_root
from jsonschema import validate as jsonschema_validate

SCHEMAS_DIR = project_root() / "schemas"

# Deal Killer 후보로 인식할 키워드. Pilot 범위에서는 Quick Report의 risk_assessment
# 원문에 이미 드러난 사실만 근거로 삼는다(임의 판단 금지) — 고도화는 Enterprise 확장 대상.
_DEAL_KILLER_KEYWORDS = ["소송", "제재", "형사", "파산", "상장폐지", "회계부정"]


@dataclass(frozen=True)
class ComparablePeer:
    peer_name: str
    ev_ebitda: float | None
    per: float | None
    pbr: float | None
    source_url: str


def _avg(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def compute_peer_average(peers: list[ComparablePeer]) -> dict:
    return {
        "ev_ebitda_avg": _avg([p.ev_ebitda for p in peers]),
        "per_avg": _avg([p.per for p in peers]),
        "pbr_avg": _avg([p.pbr for p in peers]),
        "peer_count": len(peers),
    }


def detect_deal_killers(quick_report_input: dict) -> tuple[bool, list[str]]:
    """risk_assessment 원문에서 명시적 Deal Killer 후보 문장을 찾는다."""
    reasons = [
        risk
        for risk in (quick_report_input.get("risk_assessment") or [])
        if any(keyword in risk for keyword in _DEAL_KILLER_KEYWORDS)
    ]
    return (len(reasons) > 0, reasons)


def build_estimated_valuation(
    peer_average: dict, comparable: list[ComparablePeer]
) -> dict | None:
    """Comparable 배수만으로 Valuation 근거를 만든다. 대상기업의 실제 재무수치(EBITDA/
    순이익/순자산)는 Pilot 범위에서 확인하지 않으므로, 구체적 금액 범위는 계산하지 않고
    Peer 배수 수준만 제시한다 — 임의 추정 금지."""
    if peer_average["peer_count"] == 0:
        return None

    basis_parts = []
    if peer_average["ev_ebitda_avg"] is not None:
        basis_parts.append(f"Peer 평균 EV/EBITDA {peer_average['ev_ebitda_avg']:.1f}x")
    if peer_average["per_avg"] is not None:
        basis_parts.append(f"Peer 평균 PER {peer_average['per_avg']:.1f}x")
    if peer_average["pbr_avg"] is not None:
        basis_parts.append(f"Peer 평균 PBR {peer_average['pbr_avg']:.1f}x")
    if not basis_parts:
        return None

    return {
        "basis": ", ".join(basis_parts) + " (Comparable 기반 — DCF 미사용, Enterprise Backlog)",
        "range_description": (
            "대상기업의 공개 재무수치(EBITDA/순이익/순자산)가 확인되지 않아 구체적 금액 "
            "범위는 계산하지 않았다 — Peer 배수 수준만 제시한다."
        ),
        "source_urls": [p.source_url for p in comparable if p.source_url],
    }


def determine_recommendation(
    peer_average: dict, deal_killer_found: bool, deal_killer_reasons: list[str], confidence: str
) -> dict:
    """`recommendation.signal`은 매수/매도 조언이 아니라 절차적 스크리닝 신호다."""
    if deal_killer_found:
        return {
            "signal": "decline_deal_killer_found",
            "rationale": "Deal Killer 신호 발견: " + "; ".join(deal_killer_reasons),
        }
    if peer_average["peer_count"] == 0:
        return {
            "signal": "insufficient_public_information",
            "rationale": "비교 가능한 Peer 데이터가 없어 Comparable 기반 평가를 수행할 수 없다.",
        }
    if confidence == "low":
        return {
            "signal": "monitor",
            "rationale": "공개정보 신뢰도가 낮다 — 추가 조사 후 재평가가 필요하다.",
        }
    return {
        "signal": "proceed_to_deep_review",
        "rationale": "Peer 비교와 공개정보 기준으로 심층 검토 진행을 검토할 만하다.",
    }


def build_investment_review(quick_report_input: dict, comparable: list[ComparablePeer]) -> dict:
    """Investment Review 레코드(schemas/investment_review.schema.json)를 만든다."""
    peer_average = compute_peer_average(comparable)
    deal_killer_found, deal_killer_reasons = detect_deal_killers(quick_report_input)
    confidence = quick_report_input.get("confidence", "low")
    recommendation = determine_recommendation(
        peer_average, deal_killer_found, deal_killer_reasons, confidence
    )
    estimated_valuation = build_estimated_valuation(peer_average, comparable)

    unknowns = list(quick_report_input.get("unknowns", []))
    if peer_average["peer_count"] == 0:
        unknowns.append("Comparable Peer 데이터가 없어 Valuation을 계산하지 못했다.")

    review = {
        "target_company": quick_report_input["target_company"],
        "review_date": date.today().isoformat(),
        "comparable": [
            {
                "peer_name": p.peer_name,
                "ev_ebitda": p.ev_ebitda,
                "per": p.per,
                "pbr": p.pbr,
                "source_url": p.source_url,
            }
            for p in comparable
        ],
        "peer_average": peer_average,
        "estimated_valuation": estimated_valuation,
        "strategic_fit": quick_report_input.get("lx_strategic_fit", ""),
        "synergy": list(quick_report_input.get("synergy_analysis", [])),
        "risk": list(quick_report_input.get("risk_assessment", [])),
        "deal_killer": {"found": deal_killer_found, "reasons": deal_killer_reasons},
        "recommendation": recommendation,
        "unknowns": unknowns,
        "confidence": confidence,
    }
    validate_investment_review(review)
    return review


def validate_investment_review(review: dict) -> None:
    schema = json.loads((SCHEMAS_DIR / "investment_review.schema.json").read_text(encoding="utf-8"))
    jsonschema_validate(instance=review, schema=schema)
