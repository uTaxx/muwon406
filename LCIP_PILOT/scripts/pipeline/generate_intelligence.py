"""Generate Intelligence 단계 — risk_analysis_output(Claude 출력)을 INTELLIGENCE_DB
레코드(schemas/intelligence.schema.json)로 변환한다.

사실(facts)·해석(ai_interpretation)·추론(ai_inference)·제안(recommended_actions)을 명확히
구분하는 CLAUDE.md 절대 원칙 #3을 그대로 반영한다. `risk_analysis.md` 프롬프트는 아직
"해석"과 "추론"을 하나의 `significance` 필드로만 반환하므로(리스크 분석 프롬프트 v1 범위),
이번 매핑에서는 `significance`를 `ai_interpretation`에 넣고 `ai_inference`는 빈 배열로 둔다 —
임의로 사실을 추론으로 지어내지 않기 위함이다. 프롬프트가 두 필드를 분리해 반환하도록
확장되면 이 함수만 수정하면 된다.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .ids import next_id


def build_intelligence_record(
    *,
    article_id: str,
    risk_analysis: dict,
    prompt_version: str,
    knowledge_version: str,
    existing_intelligence_ids: set[str],
    created_at: datetime | None = None,
) -> dict:
    created_at = created_at or datetime.now(timezone.utc)
    intelligence_id = next_id("INT", created_at, existing_intelligence_ids)

    return {
        "intelligence_id": intelligence_id,
        "article_ids": [article_id],
        "mission_category": risk_analysis["mission_category"],
        "intelligence_categories": risk_analysis["intelligence_categories"],
        "fact_summary": " ".join(risk_analysis["facts"]) if risk_analysis["facts"] else "",
        "verified_facts": risk_analysis["facts"],
        "importance_level": risk_analysis["importance_level"],
        "ai_interpretation": [risk_analysis["significance"]],
        "ai_inference": [],
        "lx_impact": risk_analysis["lx_impact"],
        "recommended_actions": risk_analysis["actions"],
        "unknowns": risk_analysis["unknowns"],
        "confidence_score": risk_analysis["confidence"],
        "evidence": risk_analysis["evidence"],
        "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prompt_version": prompt_version,
        "knowledge_version": knowledge_version,
    }
