import pytest

from source_priority import load_source_reliability_config, resolve_conflict, score_for_source_type

CONFIG = load_source_reliability_config()


@pytest.mark.parametrize(
    "source_type_or_name,expected_score",
    [
        ("government", 5),
        ("corporate_ir", 5),
        ("dart", 5),
        ("sec", 5),
        ("reuters", 4),
        ("google_rss", 3),
        ("blog", 2),
        ("sns", 1),
    ],
)
def test_score_for_exact_source_type(source_type_or_name, expected_score):
    assert score_for_source_type(source_type_or_name, CONFIG) == expected_score


@pytest.mark.parametrize(
    "source_name,expected_score",
    [
        ("DART 공시 (전자공시시스템)", 5),
        ("Government Press Release", 5),
        ("Reuters", 4),
        ("Google News RSS (English)", 3),
        ("Random Blog Post", 2),
        ("Twitter/X post", 1),
    ],
)
def test_score_for_source_name_via_alias(source_name, expected_score):
    assert score_for_source_type(source_name, CONFIG) == expected_score


def test_score_for_unknown_source_uses_default():
    assert score_for_source_type("완전히 알 수 없는 출처", CONFIG) == CONFIG["default_score"]


def test_resolve_conflict_picks_highest_score():
    candidates = [
        ("배상금 5백만 달러", "blog"),
        ("배상금 3백만 달러", "dart"),
        ("배상금 4백만 달러", "reuters"),
    ]
    result = resolve_conflict(candidates, CONFIG)
    assert result.fact == "배상금 3백만 달러"
    assert result.source == "dart"
    assert result.score == 5


def test_resolve_conflict_ties_keep_first_occurrence():
    candidates = [("먼저 나온 사실", "reuters"), ("나중에 나온 사실", "reuters")]
    result = resolve_conflict(candidates, CONFIG)
    assert result.fact == "먼저 나온 사실"


def test_resolve_conflict_empty_candidates_raises():
    with pytest.raises(ValueError):
        resolve_conflict([], CONFIG)
