"""Normalize 단계 — Adapter의 RawArticle을 schemas/article.schema.json 형태로 변환한다.

article_id 발급, canonical_url 기준 중복 판정(`is_new_change`), status 초기값(`collected`) 설정을
담당한다. 관련성/리스크 판단은 하지 않는다(Classify/Analyze 단계의 역할).
"""
from __future__ import annotations

from datetime import datetime, timezone

from adapters.base import RawArticle

from .ids import next_id


def normalize(
    raw: RawArticle,
    *,
    topic_id: str,
    source_type: str,
    source_reliability_grade: str,
    country: str,
    related_lx_companies: list[str],
    existing_article_ids: set[str],
    existing_canonical_urls: set[str],
    collected_at: datetime | None = None,
) -> dict:
    """RawArticle 1건을 Article 레코드(dict)로 정규화한다.

    `existing_article_ids`/`existing_canonical_urls`는 호출자가 ARTICLE_DB 현재 상태에서
    구성해 전달한다 — 이 함수는 순수 함수로 유지하고 저장소 접근은 Store 단계가 담당한다.
    """
    collected_at = collected_at or datetime.now(timezone.utc)
    collected_at_str = collected_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    canonical_url = raw.source_url
    is_new_change = canonical_url not in existing_canonical_urls

    article_id = next_id("ART", collected_at, existing_article_ids)

    return {
        "article_id": article_id,
        "topic_id": topic_id,
        "title_original": raw.title_original,
        "title_ko": None,
        "source_name": raw.source_name,
        "source_type": source_type,
        "source_url": raw.source_url,
        "canonical_url": canonical_url,
        "published_at": raw.published_at,
        "collected_at": collected_at_str,
        "language": raw.language,
        "country": country,
        "summary_ko": None,
        "litigation_amount_total": None,
        "litigation_currency": None,
        "litigation_amount_total_usd": None,
        "claimant_count": None,
        "average_amount_per_person_usd": None,
        "related_companies": [],
        "related_lx_companies": related_lx_companies,
        "event_type": "other",
        "confidence_score": 0.3,
        "source_reliability_grade": source_reliability_grade,
        "duplicate_group_id": None,
        "is_new_change": is_new_change,
        "status": "collected",
    }
