#!/usr/bin/env python3
"""Scenario 4 — 정부 정책 영향 분석 (Architect Review Round 7 신설).

`prompts/policy_analysis.md`(Round 2부터 존재했으나 Round 6까지 실제 호출자가 없었다)를
`AIProvider.analyze_policy_impact()` 신규 메서드로 실제 연결한다. 정부 RSS(SRC-0010)는
아직 `active: false` stub이라 실제 정책 기사를 수집할 수 없다 — 그래서 입력 기사는
`(예시)`로 명확히 표시한 합성 시나리오를 쓴다(DEMO_PEERS와 동일한 관례: 실제 데이터인 척
하지 않는다).

사용법: python3 scripts/scenarios/scenario_4_policy_impact.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.analyze import analyze_policy_impact
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.validate import validate_claude_output
from providers.factory import get_default_provider

# 정부 RSS(SRC-0010)가 아직 active: false stub이라 실제 정책 기사를 쓸 수 없다 — 실제
# 데이터인 척하지 않고 합성 시나리오임을 제목에 명시한다.
EXAMPLE_POLICY_ARTICLE = {
    "title_original": "[예시 시나리오] 정부 기관의 결정형 실리카(Crystalline Silica) 노출기준 강화 검토 보도",
    "source_url": "https://example.com/policy-scenario-demo",
    "source_name": "정부 보도자료 RSS (일반 카테고리, SRC-0010, 예시)",
    "published_at": "2026-08-07T00:00:00Z",
    "language": "ko",
}


def run(topic_related_companies: list[str] | None = None, verbose: bool = True) -> dict:
    """Scenario 4를 실행하고 {article, analysis}를 반환한다."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    provider = get_default_provider()
    log(f"[Scenario 4] Provider: {type(provider).__name__}")

    related_companies = topic_related_companies or ["LX_HAUSYS"]
    log("\n[1/3] Knowledge Retrieval — Government 계층 발췌 포함")
    lx_context_excerpt, knowledge_version = retrieve_context(related_companies)
    log(f"  발췌 길이: {len(lx_context_excerpt)}자")

    log("[2/3] 입력 — 정책 기사 (예시 시나리오, 실제 정부 RSS 미연동)")
    log(f"  {EXAMPLE_POLICY_ARTICLE['title_original']}")

    log("[3/3] Policy Impact Analysis")
    result = analyze_policy_impact(provider, EXAMPLE_POLICY_ARTICLE, lx_context_excerpt, "")
    validate_claude_output(result.parsed_json, "policy_analysis_output")
    log(f"  regulatory_stage={result.parsed_json['regulatory_stage']}")
    log(f"  confidence={result.parsed_json['confidence']}")

    return {"article": EXAMPLE_POLICY_ARTICLE, "analysis": result.parsed_json}


def main() -> int:
    print("=" * 70)
    print("Scenario 4 — 정부 정책 영향 분석 (예시 시나리오 입력)")
    print("=" * 70)
    run(verbose=True)
    print("\nScenario 4 완료. (참고: 정부 RSS 실연동 전까지는 예시 입력만 지원한다)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
