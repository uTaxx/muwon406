from datetime import datetime, timezone

from adapters.base import RawArticle
from pipeline.analyze import analyze_risk
from pipeline.classify import classify_relevance
from pipeline.generate_intelligence import build_intelligence_record
from pipeline.ids import next_id
from pipeline.knowledge_retrieve import retrieve_context
from pipeline.normalize import normalize
from pipeline.rule_filter import passes_rule_filter
from pipeline.validate import validate_article, validate_claude_output, validate_intelligence
from providers.mock_provider import MockProvider

TOPIC = {
    "topic_id": "TOP-0001",
    "related_lx_companies": ["LX_HAUSYS"],
    "include_keywords": ["silicosis", "engineered stone"],
    "exclude_keywords": ["sports"],
}

RAW_RELATED = RawArticle(
    title_original="Engineered stone silicosis lawsuit filed in California",
    source_url="https://example.com/silicosis-article",
    source_name="Example News",
    published_at="2026-07-30T09:00:00Z",
    language="en",
)


def test_next_id_starts_at_0001_and_increments():
    at = datetime(2026, 8, 5, tzinfo=timezone.utc)
    first = next_id("ART", at, set())
    assert first == "ART-20260805-0001"
    second = next_id("ART", at, {first})
    assert second == "ART-20260805-0002"


def test_normalize_produces_schema_valid_article_and_flags_new():
    article = normalize(
        RAW_RELATED,
        topic_id="TOP-0001",
        source_type="news_rss",
        source_reliability_grade="B",
        country="US",
        related_lx_companies=["LX_HAUSYS"],
        existing_article_ids=set(),
        existing_canonical_urls=set(),
        collected_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
    )
    validate_article(article)
    assert article["article_id"] == "ART-20260805-0001"
    assert article["is_new_change"] is True
    assert article["status"] == "collected"


def test_normalize_flags_duplicate_when_canonical_url_already_seen():
    article = normalize(
        RAW_RELATED,
        topic_id="TOP-0001",
        source_type="news_rss",
        source_reliability_grade="B",
        country="US",
        related_lx_companies=["LX_HAUSYS"],
        existing_article_ids=set(),
        existing_canonical_urls={RAW_RELATED.source_url},
        collected_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
    )
    assert article["is_new_change"] is False


def test_rule_filter_passes_include_keyword_match():
    article = {"title_original": "Engineered stone silicosis lawsuit filed"}
    assert passes_rule_filter(article, TOPIC) is True


def test_rule_filter_rejects_exclude_keyword_match():
    article = {"title_original": "Sports update: silicosis charity match"}
    assert passes_rule_filter(article, TOPIC) is False


def test_rule_filter_rejects_when_no_include_keyword_present():
    article = {"title_original": "Local weather forecast update"}
    assert passes_rule_filter(article, TOPIC) is False


def test_rule_filter_passes_everything_when_no_include_keywords_configured():
    article = {"title_original": "Anything at all"}
    assert passes_rule_filter(article, {"exclude_keywords": []}) is True


def test_classify_relevance_via_mock_provider_matches_schema():
    article = {"title_original": RAW_RELATED.title_original, "source_url": RAW_RELATED.source_url}
    result = classify_relevance(MockProvider(), article, TOPIC)
    validate_claude_output(result.parsed_json, "relevance_output")
    assert result.parsed_json["relevant"] is True


def test_retrieve_context_returns_nonempty_excerpt_and_versions_for_lx_hausys():
    excerpt, knowledge_version = retrieve_context(["LX_HAUSYS"])
    assert len(excerpt) > 0
    assert "LX_HAUSYS_COMPANY_DNA.md@" in knowledge_version


def test_retrieve_context_returns_empty_for_unknown_company():
    excerpt, knowledge_version = retrieve_context(["UNKNOWN_CO"])
    assert excerpt == ""
    assert knowledge_version == ""


def test_analyze_risk_via_mock_provider_matches_schema():
    article = {"title_original": "Engineered stone silicosis lawsuit", "source_url": "https://example.com/a"}
    result = analyze_risk(MockProvider(), article, "LX Hausys 발췌", "")
    validate_claude_output(result.parsed_json, "risk_analysis_output")


def test_build_intelligence_record_end_to_end_is_schema_valid():
    article = {"title_original": "Engineered stone silicosis lawsuit", "source_url": "https://example.com/a"}
    risk_result = analyze_risk(MockProvider(), article, "LX Hausys 발췌", "")
    record = build_intelligence_record(
        article_id="ART-20260805-0001",
        risk_analysis=risk_result.parsed_json,
        prompt_version="0.2.0",
        knowledge_version="LX_HAUSYS_COMPANY_DNA.md@0.2",
        existing_intelligence_ids=set(),
        created_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
    )
    validate_intelligence(record)
    assert record["intelligence_id"] == "INT-20260805-0001"
    assert record["article_ids"] == ["ART-20260805-0001"]
