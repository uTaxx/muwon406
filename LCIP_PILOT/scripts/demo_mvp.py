#!/usr/bin/env python3
"""TASK-017 — Pilot MVP 데모 CLI.

`tests/test_mvp_integration.py`와 동일한 흐름(Collect→Normalize→Rule Filter→Classify→
Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store→Dashboard→Test
Email/Telegram)을 콘솔에 단계별로 출력하며 실행한다. 전략팀에게 "지금 무엇이 실제로
동작하는지"를 보여주기 위한 실행형 데모다.

실제 외부 호출은 전혀 하지 않는다:
- Google RSS: tests/fixtures/sample_google_news_rss.xml을 fixture로 주입
- Claude API: MockProvider (결정론적 mock 응답)
- Gmail/Telegram: test_mode=True dry-run (실제 발송 없음)

사용법: python3 scripts/demo_mvp.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from _common import load_yaml, project_root
from adapters.google_rss_adapter import GoogleRSSAdapter
from build_dashboard import build_html
from notifiers import EmailNotifier, TelegramNotifier, build_alert_message
from pipeline.analyze import analyze_risk
from pipeline.classify import classify_relevance
from pipeline.dashboard_feed import build_dashboard_data
from pipeline.generate_intelligence import build_intelligence_record
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.normalize import normalize
from pipeline.rule_filter import passes_rule_filter
from pipeline.store import append_record, existing_ids, existing_values, load_records
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.mock_provider import MockProvider

FIXTURE_RSS = project_root() / "tests" / "fixtures" / "sample_google_news_rss.xml"


def step(n: int, title: str) -> None:
    print(f"\n[{n}/10] {title}")


def main() -> int:
    print("=" * 70)
    print("LCIP Pilot — MVP 데모 (전 구간 Mock/dry-run, 실제 외부 호출 없음)")
    print("=" * 70)

    topic = load_yaml("config/topics.yaml")["topics"][0]
    source_config = load_yaml("config/sources.yaml")["sources"][0]
    now = datetime.now(timezone.utc)

    out_dir = project_root() / "output" / "demo_mvp"
    out_dir.mkdir(parents=True, exist_ok=True)
    article_db = out_dir / "ARTICLE_DB.jsonl"
    intelligence_db = out_dir / "INTELLIGENCE_DB.jsonl"

    step(1, "Collect — Google News RSS (fixture 주입, 실제 네트워크 호출 없음)")
    rss_text = FIXTURE_RSS.read_text(encoding="utf-8")
    adapter = GoogleRSSAdapter(source_config, enabled=True, http_get=lambda url: rss_text)
    raw_articles = adapter.collect("engineered stone silicosis")
    print(f"  수집: {len(raw_articles)}건")
    silica_raw = next(r for r in raw_articles if "silicosis" in r.title_original.lower())
    print(f"  대상 기사: {silica_raw.title_original}")

    step(2, "Normalize — Article 스키마로 정규화")
    article = normalize(
        silica_raw,
        topic_id=topic["topic_id"],
        source_type="news_rss",
        source_reliability_grade=source_config["reliability_grade"],
        country=source_config["country"],
        related_lx_companies=topic["related_lx_companies"],
        existing_article_ids=existing_ids(article_db, "article_id"),
        existing_canonical_urls=existing_values(article_db, "canonical_url"),
        collected_at=now,
    )
    validate_article(article)
    print(f"  article_id={article['article_id']}  is_new_change={article['is_new_change']}")

    step(3, "Rule Filter — AI 호출 없이 1차 판정")
    passed = passes_rule_filter(article, topic)
    print(f"  통과 여부: {passed}")
    if not passed:
        print("  규칙 필터에서 탈락 — 데모 중단 (fixture 기사는 통과하도록 구성되어 있음)")
        return 1

    step(4, "Classify — 관련성 분류 (MockProvider)")
    provider = MockProvider()
    classify_result = classify_relevance(provider, article, topic)
    validate_claude_output(classify_result.parsed_json, "relevance_output")
    print(f"  relevant={classify_result.parsed_json['relevant']}"
          f"  needs_deep_analysis={classify_result.parsed_json['needs_deep_analysis']}")

    step(5, "Knowledge Retrieve — LX Hausys Knowledge Base 발췌")
    lx_context_excerpt, knowledge_version = retrieve_context(topic["related_lx_companies"])
    print(f"  발췌 길이: {len(lx_context_excerpt)}자, knowledge_version={knowledge_version[:60]}...")

    step(6, "Analyze — 심층 리스크 분석 (MockProvider)")
    analyze_result = analyze_risk(provider, article, lx_context_excerpt, "")
    validate_claude_output(analyze_result.parsed_json, "risk_analysis_output")
    print(f"  confidence={analyze_result.parsed_json['confidence']}")

    step(7, "Generate Intelligence — INTELLIGENCE_DB 레코드 생성")
    intelligence = build_intelligence_record(
        article_id=article["article_id"],
        risk_analysis=analyze_result.parsed_json,
        prompt_version="0.2.0",
        knowledge_version=knowledge_version,
        existing_intelligence_ids=existing_ids(intelligence_db, "intelligence_id"),
        created_at=now,
    )
    validate_intelligence(intelligence)
    print(f"  intelligence_id={intelligence['intelligence_id']}")

    step(8, "Store — ARTICLE_DB/INTELLIGENCE_DB 저장 (로컬 JSONL, dry-run 스탠드인)")
    append_record(article_db, article)
    append_record(intelligence_db, intelligence)
    print(f"  {article_db}")
    print(f"  {intelligence_db}")

    step(9, "Dashboard 반영 — 정적 HTML 빌드")
    dashboard_data = build_dashboard_data(
        topic_display_name=topic["display_name"],
        generated_at_kst=now.strftime("%Y-%m-%d %H:%M"),
        articles=load_records(article_db),
        intelligences=load_records(intelligence_db),
    )
    html = build_html(dashboard_data)
    dashboard_path = out_dir / "dashboard.html"
    dashboard_path.write_text(html, encoding="utf-8")
    print(f"  {dashboard_path}")

    step(10, "Test Email / Test Telegram — dry-run (test_mode=True, 실제 발송 없음)")
    subject, body = build_alert_message(article, intelligence)
    notification_config = load_yaml("config/notification.yaml")
    email_result = EmailNotifier(notification_config).send(subject, body)
    telegram_result = TelegramNotifier(notification_config).send(subject, body)
    print(f"  [Email]    sent={email_result.sent} recipient={email_result.recipient}")
    print(f"  [Telegram] sent={telegram_result.sent} recipient={telegram_result.recipient}")
    print(f"\n  제목: {subject}")
    print(f"  본문:\n{body}")

    print("\n" + "=" * 70)
    print("Pilot MVP 성공 기준 충족: Collect→Normalize→Rule Filter→Classify→"
          "Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store→"
          "Dashboard→Test Email→Test Telegram 전 단계 정상 동작 (Mock 기반)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
