#!/usr/bin/env python3
"""뉴스 수집 실체화 라운드(2026-08-08) 신설 — 실제 다건·다중소스 배치 오케스트레이션.

`scripts/scenarios/scenario_1_news_analysis.py`는 fixture 1건짜리 데모/테스트
하네스였을 뿐 실제 운영 흐름이 아니었다 — 이 스크립트가 처음으로 "활성 Keyword
Group × 활성 Source"를 전부 순회하는 실제 배치 흐름이다.

흐름: Collect(그룹별 쿼리) → Normalize → Rule Filter(그룹별 매칭) → **전체 ARTICLE_DB
적재**(매칭 안 돼도 status="rejected"로 적재 — "전체 리스트는 데이터로 계속 축적"
요구사항) → Haiku Classify(매칭된 것만) → Sonnet Analyze(needs_deep_analysis인 것만,
매칭된 첫 번째 그룹의 ai_instructions를 Dynamic Block에 전달) → INTELLIGENCE_DB 적재 →
Dashboard 갱신 → 다이제스트 발송(기본 dry-run, `notification.yaml`의 test_mode 존중).

실제 외부 호출 여부는 기존 안전장치를 그대로 따른다 — `feature_flags.yaml`의
`real_network_calls`/`claude_api_enabled`/`notification_send_enabled`가 꺼져 있으면
Adapter/Provider/Notifier가 각자 안전하게 멈추거나 Mock/dry-run으로 동작한다. 이
스크립트 자체는 어떤 것도 강제로 켜지 않는다.

사용법: python3 scripts/run_news_collection.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import load_yaml, project_root
from adapters.base import SourceAdapter, SourceAdapterDisabledError
from adapters.google_rss_adapter import GoogleRSSAdapter
from adapters.naver_news_adapter import NaverNewsAdapter
from build_dashboard import build_html
from dashboard_data_provider import PipelineDashboardDataProvider
from keyword_groups import active_keyword_groups
from notifiers import EmailNotifier, TelegramNotifier, build_digest_message
from pipeline.analyze import analyze_risk
from pipeline.classify import classify_relevance
from pipeline.generate_intelligence import build_intelligence_record
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.normalize import normalize
from pipeline.rule_filter import passes_rule_filter_groups
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.factory import get_default_provider
from storage.local_jsonl_storage import LocalJSONLStorage

ARTICLE_DB, INTELLIGENCE_DB = "ARTICLE_DB", "INTELLIGENCE_DB"

_ADAPTER_CLASSES: dict[str, type[SourceAdapter]] = {
    "SRC-0001": GoogleRSSAdapter,
    "SRC-0002": GoogleRSSAdapter,
    "SRC-0003": NaverNewsAdapter,
}


def build_group_query(group: dict) -> str:
    """그룹의 include_keywords를 OR로 묶은 검색어를 만든다. 여러 단어로 된 키워드는
    따옴표로 감싸 구(phrase) 검색이 되게 한다."""
    terms = [f'"{kw}"' if " " in kw else kw for kw in group["include_keywords"]]
    return " OR ".join(terms)


def run(
    *,
    provider=None,
    adapters_by_source_id: dict[str, SourceAdapter] | None = None,
    groups: list[dict] | None = None,
    email_notifier: EmailNotifier | None = None,
    telegram_notifier: TelegramNotifier | None = None,
    storage: LocalJSONLStorage | None = None,
    now: datetime | None = None,
    verbose: bool = True,
) -> dict:
    """배치 1회 실행. {collected, stored, classified, analyzed, digest_records,
    email_result, telegram_result, dashboard_path}를 반환한다."""

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    now = now or datetime.now(timezone.utc)
    provider = provider or get_default_provider()
    groups = groups if groups is not None else active_keyword_groups()
    storage = storage or LocalJSONLStorage(project_root() / "output" / "pilot_data")
    email_notifier = email_notifier or EmailNotifier()
    telegram_notifier = telegram_notifier or TelegramNotifier()

    sources_by_id = {s["source_id"]: s for s in load_yaml("config/sources.yaml")["sources"]}
    topics_by_id = {t["topic_id"]: t for t in load_yaml("config/topics.yaml")["topics"]}

    log(f"[뉴스 수집] Provider: {type(provider).__name__}, 활성 그룹 {len(groups)}개")

    counters = {"collected": 0, "stored": 0, "classified": 0, "analyzed": 0}
    digest_records: list[tuple[dict, dict]] = []
    seen_canonical_urls: set[str] = set()

    for group in groups:
        for source_id in group["sources"]:
            source_config = sources_by_id.get(source_id)
            if source_config is None or not source_config.get("active"):
                log(f"  [건너뜀] {source_id}: 미등록 또는 active=false")
                continue

            adapter = (adapters_by_source_id or {}).get(source_id)
            if adapter is None:
                adapter_cls = _ADAPTER_CLASSES.get(source_id)
                if adapter_cls is None:
                    log(f"  [건너뜀] {source_id}: 지원하는 Adapter 없음")
                    continue
                adapter = adapter_cls(source_config)

            query = build_group_query(group)
            try:
                raw_articles = adapter.collect(query)
            except SourceAdapterDisabledError as exc:
                log(f"  [건너뜀] {group['group_id']}/{source_id}: {exc}")
                continue

            topic = topics_by_id.get(group["topic_id"], {})
            for raw in raw_articles:
                if raw.source_url in seen_canonical_urls:
                    continue
                seen_canonical_urls.add(raw.source_url)
                counters["collected"] += 1

                article = normalize(
                    raw,
                    topic_id=group["topic_id"],
                    source_type=source_config.get("source_type", "other"),
                    source_reliability_grade=source_config.get("reliability_grade", "C"),
                    country=source_config.get("country", "multi"),
                    related_lx_companies=topic.get("related_lx_companies", []),
                    existing_article_ids=storage.existing_ids(ARTICLE_DB, "article_id"),
                    existing_canonical_urls=storage.existing_values(ARTICLE_DB, "canonical_url"),
                    collected_at=now,
                )

                matched_group_ids = passes_rule_filter_groups(article, [group])
                if not matched_group_ids:
                    article["status"] = "rejected"
                    validate_article(article)
                    storage.append(ARTICLE_DB, article)
                    counters["stored"] += 1
                    continue

                classify_result = classify_relevance(provider, article, topic)
                validate_claude_output(classify_result.parsed_json, "relevance_output")

                if not classify_result.parsed_json["relevant"]:
                    article["status"] = "rejected"
                    validate_article(article)
                    storage.append(ARTICLE_DB, article)
                    counters["stored"] += 1
                    continue

                article["status"] = "classified"
                counters["classified"] += 1

                if classify_result.parsed_json["needs_deep_analysis"]:
                    lx_context_excerpt, knowledge_version = retrieve_context(
                        topic.get("related_lx_companies", [])
                    )
                    analyze_result = analyze_risk(
                        provider, article, lx_context_excerpt, "",
                        group_ai_instructions=group.get("ai_instructions", ""),
                    )
                    validate_claude_output(analyze_result.parsed_json, "risk_analysis_output")

                    intelligence = build_intelligence_record(
                        article_id=article["article_id"],
                        risk_analysis=analyze_result.parsed_json,
                        prompt_version="0.4.0",
                        knowledge_version=knowledge_version,
                        existing_intelligence_ids=storage.existing_ids(
                            INTELLIGENCE_DB, "intelligence_id"
                        ),
                        created_at=now,
                    )
                    validate_intelligence(intelligence)
                    article["status"] = "analyzed"
                    counters["analyzed"] += 1

                    storage.append(INTELLIGENCE_DB, intelligence)
                    digest_records.append((article, intelligence))
                    log(
                        f"  [분석완료] {article['title_original']} "
                        f"(importance={intelligence['importance_level']})"
                    )

                validate_article(article)
                storage.append(ARTICLE_DB, article)
                counters["stored"] += 1

    log(
        f"[집계] 수집 {counters['collected']}건 / 적재 {counters['stored']}건 / "
        f"관련 분류 {counters['classified']}건 / 심층분석 {counters['analyzed']}건"
    )

    data_provider = PipelineDashboardDataProvider(
        storage,
        topic_display_name="엔지니어드스톤·실리코시스",
        generated_at_kst=now.strftime("%Y-%m-%d %H:%M"),
    )
    html = build_html(data_provider.get_data())
    dashboard_path = storage.base_dir / "dashboard.html"
    dashboard_path.write_text(html, encoding="utf-8")
    log(f"[대시보드] {dashboard_path}")

    subject, body = build_digest_message(digest_records)
    email_result = email_notifier.send(subject, body)
    telegram_result = telegram_notifier.send(subject, body)
    log(f"[다이제스트] {subject}")

    return {
        "counters": counters,
        "digest_records": digest_records,
        "email_result": email_result,
        "telegram_result": telegram_result,
        "dashboard_path": str(dashboard_path),
    }


def main() -> int:
    print("=" * 70)
    print("뉴스 수집 실체화 — 실제 배치 파이프라인")
    print("=" * 70)
    run(verbose=True)
    print("\n완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
