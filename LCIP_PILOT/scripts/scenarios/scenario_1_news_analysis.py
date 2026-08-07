#!/usr/bin/env python3
"""Scenario 1 — 뉴스 분석 (Architect Review Round 7).

뉴스수집(Collect)→Rule Filter→Knowledge Retrieval→Claude Analysis→INTELLIGENCE_DB→
Dashboard까지, Round 6 `demo_pilot.py`의 전반부를 독립 실행 가능한 Scenario로 분리한
것이다. 다른 Scenario에 의존하지 않고 단독으로 실행된다.

실제 외부 호출 없음: Google RSS는 fixture 주입, Claude는
`providers.factory.get_default_provider()`(Key/Flag 미충족 시 MockProvider로 자동 귀결).

사용법: python3 scripts/scenarios/scenario_1_news_analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# scripts/scenarios/*.py는 scripts/*.py의 형제 모듈(_common, providers 등)을 직접
# import한다 — 단독 실행(`python3 scripts/scenarios/scenario_N.py`) 시에는 Python이
# 이 파일의 부모 디렉터리(scripts/scenarios/)만 sys.path에 넣기 때문에, tests/conftest.py가
# pytest에서 하는 것과 동일하게 scripts/ 자체를 sys.path에 추가해야 한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone

from _common import load_yaml, project_root
from adapters.google_rss_adapter import GoogleRSSAdapter
from build_dashboard import build_html
from dashboard_data_provider import PipelineDashboardDataProvider
from pipeline.analyze import analyze_risk
from pipeline.classify import classify_relevance
from pipeline.generate_intelligence import build_intelligence_record
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.normalize import normalize
from pipeline.rule_filter import passes_rule_filter
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.factory import get_default_provider
from storage.local_jsonl_storage import LocalJSONLStorage

FIXTURE_RSS = project_root() / "tests" / "fixtures" / "sample_google_news_rss.xml"
ARTICLE_DB, INTELLIGENCE_DB = "ARTICLE_DB", "INTELLIGENCE_DB"


def run(verbose: bool = True) -> dict:
    """Scenario 1을 실행하고 {article, intelligence, dashboard_path}를 반환한다."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    provider = get_default_provider()
    log(f"[Scenario 1] Provider: {type(provider).__name__}")

    topic = load_yaml("config/topics.yaml")["topics"][0]
    source_config = load_yaml("config/sources.yaml")["sources"][0]
    now = datetime.now(timezone.utc)

    out_dir = project_root() / "output" / "scenario_1_news_analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    storage = LocalJSONLStorage(out_dir)

    log("\n[1/6] Collect — Google News RSS (fixture 주입)")
    rss_text = FIXTURE_RSS.read_text(encoding="utf-8")
    adapter = GoogleRSSAdapter(source_config, enabled=True, http_get=lambda url: rss_text)
    raw_articles = adapter.collect("engineered stone silicosis")
    silica_raw = next(r for r in raw_articles if "silicosis" in r.title_original.lower())
    log(f"  대상 기사: {silica_raw.title_original}")

    article = normalize(
        silica_raw,
        topic_id=topic["topic_id"],
        source_type="news_rss",
        source_reliability_grade=source_config["reliability_grade"],
        country=source_config["country"],
        related_lx_companies=topic["related_lx_companies"],
        existing_article_ids=storage.existing_ids(ARTICLE_DB, "article_id"),
        existing_canonical_urls=storage.existing_values(ARTICLE_DB, "canonical_url"),
        collected_at=now,
    )
    validate_article(article)

    log("[2/6] Rule Filter")
    if not passes_rule_filter(article, topic):
        raise RuntimeError("Rule Filter에서 탈락 — fixture 기사는 통과하도록 구성되어 있어야 한다")

    classify_result = classify_relevance(provider, article, topic)
    validate_claude_output(classify_result.parsed_json, "relevance_output")
    log(f"  relevant={classify_result.parsed_json['relevant']}")

    log("[3/6] Knowledge Retrieval")
    lx_context_excerpt, knowledge_version = retrieve_context(topic["related_lx_companies"])
    log(f"  발췌 길이: {len(lx_context_excerpt)}자")

    log("[4/6] Claude Analysis")
    analyze_result = analyze_risk(provider, article, lx_context_excerpt, "")
    validate_claude_output(analyze_result.parsed_json, "risk_analysis_output")
    log(f"  confidence={analyze_result.parsed_json['confidence']}")

    log("[5/6] INTELLIGENCE_DB")
    intelligence = build_intelligence_record(
        article_id=article["article_id"],
        risk_analysis=analyze_result.parsed_json,
        prompt_version="0.2.0",
        knowledge_version=knowledge_version,
        existing_intelligence_ids=storage.existing_ids(INTELLIGENCE_DB, "intelligence_id"),
        created_at=now,
    )
    validate_intelligence(intelligence)
    storage.append(ARTICLE_DB, article)
    storage.append(INTELLIGENCE_DB, intelligence)
    log(f"  intelligence_id={intelligence['intelligence_id']}")

    log("[6/6] Dashboard")
    data_provider = PipelineDashboardDataProvider(
        storage, topic_display_name=topic["display_name"],
        generated_at_kst=now.strftime("%Y-%m-%d %H:%M"),
    )
    html = build_html(data_provider.get_data())
    dashboard_path = out_dir / "dashboard.html"
    dashboard_path.write_text(html, encoding="utf-8")
    log(f"  {dashboard_path}")

    return {"article": article, "intelligence": intelligence, "dashboard_path": str(dashboard_path)}


def main() -> int:
    print("=" * 70)
    print("Scenario 1 — 뉴스 분석")
    print("=" * 70)
    run(verbose=True)
    print("\nScenario 1 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
