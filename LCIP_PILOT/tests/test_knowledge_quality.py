from datetime import date

import knowledge_quality


def test_na_layer_counts_as_reliable():
    text = """## 1. Company — 개요

내용

- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A
"""
    layers = knowledge_quality.parse_layers(text)
    assert len(layers) == 1
    assert layers[0].is_na is True
    assert layers[0].reliable is True


def test_unset_layer_is_not_reliable():
    text = """## 1. Company — 개요

TODO: source required

- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)
"""
    layers = knowledge_quality.parse_layers(text)
    assert layers[0].reliable is False


def test_fresh_confirmed_layer_is_reliable():
    text = """## 1. Company — 개요

확인된 사실

- Source: DART / Reference URL: https://example.com/dart / Confidence: high / Last Verified: 2026-08-01
"""
    layers = knowledge_quality.parse_layers(text, today=date(2026, 8, 5))
    assert layers[0].reliable is True


def test_stale_layer_is_not_reliable():
    text = """## 1. Company — 개요

오래된 확인

- Source: DART / Reference URL: https://example.com/dart / Confidence: high / Last Verified: 2020-01-01
"""
    layers = knowledge_quality.parse_layers(text, today=date(2026, 8, 5))
    assert layers[0].reliable is False


def test_score_document_current_repo_state_is_between_0_and_100():
    for filename in knowledge_quality.COMPANY_PROFILE_DOCS:
        score, layers = knowledge_quality.score_document(filename)
        assert 0.0 <= score <= 100.0
        assert len(layers) == 12


def test_holdings_context_scores_higher_due_to_na_layers():
    dna_score, _ = knowledge_quality.score_document("LX_HAUSYS_COMPANY_DNA.md")
    holdings_score, _ = knowledge_quality.score_document("LX_HOLDINGS_CONTEXT.md")
    assert holdings_score > dna_score
