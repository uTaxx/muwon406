"""TASK-017 — Pilot MVP 통합 테스트.

Architect Review Round 4가 정의한 Pilot MVP 성공 기준을 그대로 코드로 검증한다:
    Google RSS -> 1건 이상 기사 수집 -> Rule Filter -> Claude 분석(Mock) ->
    INTELLIGENCE_DB 저장 -> Dashboard 반영 -> Test Email -> Test Telegram

전 구간 실제 외부 호출 없음(RSS는 fixture 주입, Claude는 MockProvider, 발송은
test_mode dry-run) — CLAUDE.md 절대 원칙 #8 및 Round 4 "Mock 기반으로 구조와 테스트를
먼저 완성한다" 지시를 그대로 지킨다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from _common import load_yaml
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
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.mock_provider import MockProvider
from storage.local_jsonl_storage import LocalJSONLStorage

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_RSS_TEXT = (ROOT / "tests" / "fixtures" / "sample_google_news_rss.xml").read_text(
    encoding="utf-8"
)


def test_pilot_mvp_end_to_end_flow(tmp_path):
    topic = load_yaml("config/topics.yaml")["topics"][0]
    assert topic["topic_id"] == "TOP-0001"
    source_config = load_yaml("config/sources.yaml")["sources"][0]
    assert source_config["source_id"] == "SRC-0001"

    # Round 5: Pipeline은 StorageBackend만 참조한다.
    storage = LocalJSONLStorage(tmp_path)
    ARTICLE_DB, INTELLIGENCE_DB = "ARTICLE_DB", "INTELLIGENCE_DB"
    now = datetime(2026, 8, 5, tzinfo=timezone.utc)

    # 1. Collect — Google RSS (fixture 주입, 실제 네트워크 호출 없음)
    adapter = GoogleRSSAdapter(source_config, enabled=True, http_get=lambda url: SAMPLE_RSS_TEXT)
    raw_articles = adapter.collect("engineered stone silicosis")
    assert len(raw_articles) >= 1

    silica_raw = next(r for r in raw_articles if "silicosis" in r.title_original.lower())

    # 2. Normalize
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
    assert article["is_new_change"] is True

    # 3. Rule Filter — AI 호출 없이 1차로 통과 여부를 가른다
    assert passes_rule_filter(article, topic) is True

    # 4. Classify — Claude 분석(Mock)
    provider = MockProvider()
    classify_result = classify_relevance(provider, article, topic)
    validate_claude_output(classify_result.parsed_json, "relevance_output")
    assert classify_result.parsed_json["relevant"] is True
    assert classify_result.parsed_json["needs_deep_analysis"] is True

    # 5. Knowledge Retrieve
    lx_context_excerpt, knowledge_version = retrieve_context(topic["related_lx_companies"])
    assert len(lx_context_excerpt) > 0
    assert knowledge_version != ""

    # 6. Analyze — 심층 리스크 분석(Mock)
    analyze_result = analyze_risk(provider, article, lx_context_excerpt, "")
    validate_claude_output(analyze_result.parsed_json, "risk_analysis_output")
    assert provider.call_count == 2

    # 7. Generate Intelligence
    intelligence = build_intelligence_record(
        article_id=article["article_id"],
        risk_analysis=analyze_result.parsed_json,
        prompt_version="0.2.0",
        knowledge_version=knowledge_version,
        existing_intelligence_ids=storage.existing_ids(INTELLIGENCE_DB, "intelligence_id"),
        created_at=now,
    )
    validate_intelligence(intelligence)

    # 8. Store — StorageBackend(LocalJSONLStorage)에 저장 (Google Sheets의 dry-run 스탠드인)
    storage.append(ARTICLE_DB, article)
    storage.append(INTELLIGENCE_DB, intelligence)
    stored_articles = storage.load_all(ARTICLE_DB)
    stored_intelligences = storage.load_all(INTELLIGENCE_DB)
    assert len(stored_articles) == 1
    assert len(stored_intelligences) == 1
    assert stored_intelligences[0]["article_ids"] == [article["article_id"]]

    # 9. Dashboard 반영 (Round 8: Executive Dashboard — Today's Intelligence/Critical Risk)
    dashboard_data = build_dashboard_data(
        topic_display_name=topic["display_name"],
        generated_at_kst="2026-08-05 09:00",
        articles=stored_articles,
        intelligences=stored_intelligences,
    )
    assert len(dashboard_data["today_intelligence"]) == 1
    assert article["title_original"] in dashboard_data["today_intelligence"][0]["핵심 내용"]
    assert len(dashboard_data["critical_risk"]) == 1  # MockProvider가 항상 risk_management로 분류
    html = build_html(dashboard_data)
    assert article["title_original"] in html
    assert "{{" not in html

    # 10. Test Email / Test Telegram — dry-run(test_mode=True), 실제 발송 없음
    subject, body = build_alert_message(article, intelligence)
    notification_config = {
        "notifications": {"test_mode": True, "email_enabled": True, "telegram_enabled": True},
        "email": {"recipient_env": "LCIP_TEST_EMAIL_RECIPIENT"},
        "telegram": {"chat_id_env": "TELEGRAM_CHAT_ID"},
    }
    email_result = EmailNotifier(notification_config).send(subject, body)
    telegram_result = TelegramNotifier(notification_config).send(subject, body)
    assert email_result.sent is False and email_result.test_mode is True
    assert telegram_result.sent is False and telegram_result.test_mode is True
    assert article["title_original"] in subject
