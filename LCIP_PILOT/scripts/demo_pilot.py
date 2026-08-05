#!/usr/bin/env python3
"""TASK-017 — LCIP Pilot 통합 데모 CLI (Round 6: 2개 데모를 1개로 통합).

Round 4/5의 `scripts/demo_mvp.py`(뉴스 파이프라인)와 `scripts/demo_quick_scan.py`
(Quick Company Scan/Investment Review)를 하나의 명령으로 합쳤다 — Architect Review
Round 6 지시: "Pilot Demo를 2개에서 1개로 통합. 최종 시나리오: 뉴스수집→Rule Filter→
Knowledge Retrieval→Claude Analysis→INTELLIGENCE_DB→Dashboard→Quick Company Scan→
Investment Review→Email Preview→Telegram Preview, 하나의 명령으로 실행." 이 파일이 그
순서를 그대로 따른다.

실제 외부 호출은 전혀 하지 않는다:
- Google RSS: tests/fixtures/sample_google_news_rss.xml을 fixture로 주입
- Claude API: `providers.factory.get_default_provider()` — ANTHROPIC_API_KEY 미설정
  + feature_flags.claude_api_enabled=false(현재 기본값)이므로 항상 MockProvider로 귀결된다.
  다음 Architect 승인 후 Key/Flag를 켜면 이 데모는 코드 수정 없이 실제 Claude를 호출한다.
- Gmail/Telegram: test_mode=True dry-run (실제 발송 없음)

사용법: python3 scripts/demo_pilot.py ["Quick Scan 대상 회사명"]
        (인자를 생략하면 config/company_registry.yaml에 등록된 "LX Hausys"로 실행)
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from _common import load_yaml, project_root
from adapters.google_rss_adapter import GoogleRSSAdapter
from build_dashboard import build_html
from dashboard_data_provider import PipelineDashboardDataProvider
from investment_review import ComparablePeer, build_investment_review
from notifiers import EmailNotifier, TelegramNotifier, build_alert_message
from pipeline.analyze import analyze_risk
from pipeline.classify import classify_relevance
from pipeline.generate_intelligence import build_intelligence_record
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.normalize import normalize
from pipeline.rule_filter import passes_rule_filter
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.factory import get_default_provider
from quick_company_scan import (
    build_investment_review_input,
    build_quick_report,
    generate_company_intelligence,
    resolve_company_input,
    select_sources_for_company,
)
from storage.local_jsonl_storage import LocalJSONLStorage

FIXTURE_RSS = project_root() / "tests" / "fixtures" / "sample_google_news_rss.xml"

# 데모용 Comparable Peer 예시(공개 배수를 실제로 조회하지 않았음을 명시) — 실제 서비스에서는
# Knowledge Retrieval Engine/외부 데이터로 채워야 한다.
DEMO_PEERS = [
    ComparablePeer("Peer A (예시)", ev_ebitda=8.5, per=13.0, pbr=1.4, source_url="https://example.com/peer-a"),
    ComparablePeer("Peer B (예시)", ev_ebitda=9.5, per=15.0, pbr=1.6, source_url="https://example.com/peer-b"),
]

TOTAL_STEPS = 10


def step(n: int, title: str) -> None:
    print(f"\n[{n}/{TOTAL_STEPS}] {title}")


def main() -> int:
    quick_scan_query = sys.argv[1] if len(sys.argv) > 1 else "LX Hausys"

    print("=" * 70)
    print("LCIP Pilot — 통합 데모 (전 구간 Mock/dry-run, 실제 외부 호출 없음)")
    print("=" * 70)

    provider = get_default_provider()
    print(f"Provider: {type(provider).__name__} "
          f"(ANTHROPIC_API_KEY/feature_flags.claude_api_enabled 둘 다 참일 때만 ClaudeProvider)")

    topic = load_yaml("config/topics.yaml")["topics"][0]
    source_config = load_yaml("config/sources.yaml")["sources"][0]
    now = datetime.now(timezone.utc)

    out_dir = project_root() / "output" / "demo_pilot"
    out_dir.mkdir(parents=True, exist_ok=True)
    storage = LocalJSONLStorage(out_dir)
    ARTICLE_DB, INTELLIGENCE_DB = "ARTICLE_DB", "INTELLIGENCE_DB"

    step(1, "뉴스수집(Collect) — Google News RSS (fixture 주입, 실제 네트워크 호출 없음)")
    rss_text = FIXTURE_RSS.read_text(encoding="utf-8")
    adapter = GoogleRSSAdapter(source_config, enabled=True, http_get=lambda url: rss_text)
    raw_articles = adapter.collect("engineered stone silicosis")
    print(f"  수집: {len(raw_articles)}건")
    silica_raw = next(r for r in raw_articles if "silicosis" in r.title_original.lower())
    print(f"  대상 기사: {silica_raw.title_original}")

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
    print(f"  article_id={article['article_id']}  is_new_change={article['is_new_change']}")

    step(2, "Rule Filter — AI 호출 없이 1차 판정")
    passed = passes_rule_filter(article, topic)
    print(f"  통과 여부: {passed}")
    if not passed:
        print("  규칙 필터에서 탈락 — 데모 중단 (fixture 기사는 통과하도록 구성되어 있음)")
        return 1

    classify_result = classify_relevance(provider, article, topic)
    validate_claude_output(classify_result.parsed_json, "relevance_output")
    print(f"  [Classify] relevant={classify_result.parsed_json['relevant']}"
          f"  needs_deep_analysis={classify_result.parsed_json['needs_deep_analysis']}")

    step(3, "Knowledge Retrieval — LX Hausys Knowledge Base 발췌")
    lx_context_excerpt, knowledge_version = retrieve_context(topic["related_lx_companies"])
    print(f"  발췌 길이: {len(lx_context_excerpt)}자, knowledge_version={knowledge_version[:60]}...")

    step(4, "Claude Analysis — 심층 리스크 분석")
    analyze_result = analyze_risk(provider, article, lx_context_excerpt, "")
    validate_claude_output(analyze_result.parsed_json, "risk_analysis_output")
    print(f"  confidence={analyze_result.parsed_json['confidence']}")

    step(5, "INTELLIGENCE_DB — 레코드 생성 및 저장")
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
    print(f"  intelligence_id={intelligence['intelligence_id']}")
    print(f"  {out_dir / (ARTICLE_DB + '.jsonl')}")
    print(f"  {out_dir / (INTELLIGENCE_DB + '.jsonl')}")

    step(6, "Dashboard 반영 — Data Provider → Widget → Dashboard")
    data_provider = PipelineDashboardDataProvider(
        storage,
        topic_display_name=topic["display_name"],
        generated_at_kst=now.strftime("%Y-%m-%d %H:%M"),
    )
    dashboard_data = data_provider.get_data()
    html = build_html(dashboard_data)
    dashboard_path = out_dir / "dashboard.html"
    dashboard_path.write_text(html, encoding="utf-8")
    print(f"  {dashboard_path}")

    step(7, f"Quick Company Scan — Resolve Company Input ('{quick_scan_query}')")
    company = resolve_company_input(quick_scan_query)
    print(f"  resolved={company.resolved}  company_id={company.company_id}")
    if not company.resolved:
        print("  주의: config/company_registry.yaml에 등록되지 않은 회사 — 임의로 정보를")
        print("        지어내지 않고 그대로 진행한다(Provider가 unknowns에 정직하게 남김).")

    sources = select_sources_for_company(company)
    for s in sources:
        print(f"  - {s['source_id']}: {s['source_name']} (active={s.get('active')})")

    scan_result = generate_company_intelligence(provider, company, sources)
    quick_report = build_quick_report(company, scan_result)
    print(f"  target_company={quick_report['target_company']}  confidence={quick_report['confidence']}")

    step(8, "Investment Review — Comparable 기반 Valuation (DCF 미사용)")
    review_input = build_investment_review_input(quick_report)
    review = build_investment_review(review_input, DEMO_PEERS)
    print(f"  peer_average: {review['peer_average']}")
    if review["estimated_valuation"]:
        print(f"  estimated_valuation.basis: {review['estimated_valuation']['basis']}")
    print(f"  deal_killer.found: {review['deal_killer']['found']}")
    print(f"  recommendation.signal: {review['recommendation']['signal']}")

    step(9, "Email Preview — dry-run (test_mode=True, 실제 발송 없음)")
    subject, body = build_alert_message(article, intelligence)
    notification_config = load_yaml("config/notification.yaml")
    email_result = EmailNotifier(notification_config).send(subject, body)
    print(f"  sent={email_result.sent} recipient={email_result.recipient}")
    print(f"  제목: {subject}")

    step(10, "Telegram Preview — dry-run (test_mode=True, 실제 발송 없음)")
    telegram_result = TelegramNotifier(notification_config).send(subject, body)
    print(f"  sent={telegram_result.sent} recipient={telegram_result.recipient}")
    print(f"  본문:\n{body}")

    print("\n" + "=" * 70)
    print("Pilot 통합 데모 성공 기준 충족: 뉴스수집→Rule Filter→Knowledge Retrieval→"
          "Claude Analysis→INTELLIGENCE_DB→Dashboard→Quick Company Scan→Investment "
          "Review→Email Preview→Telegram Preview 전 단계 정상 동작")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
