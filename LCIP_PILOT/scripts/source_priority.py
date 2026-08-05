"""Source Reliability Score — Architect Review Round 5 신설.

Source 유형(정부/기업IR/DART/SEC/로이터/Google RSS/블로그/SNS)별 1~5 신뢰도 점수와
"동일 사실이 충돌할 때 점수가 높은 근거를 우선한다"는 규칙을 구현한다.

기존 `config/sources.yaml`의 `reliability_grade`(A/B/C, Source 단위 고정값,
`knowledge/SOURCE_PRIORITY.md`에 정의됨)와는 별도 축이다 — 이 모듈은 그보다 세분화된
점수를 제공하며, Knowledge Retrieval Engine(`scripts/knowledge_engine.py`)의
source-priority 검색과 향후 AI 사실 충돌 해소 로직에 쓰인다.
"""
from __future__ import annotations

from dataclasses import dataclass

from _common import load_yaml


def load_source_reliability_config() -> dict:
    return load_yaml("config/source_reliability.yaml")


def score_for_source_type(source_type_or_name: str, config: dict | None = None) -> int:
    """source_type 또는 source_name 문자열을 받아 1~5 Source Reliability Score를 반환한다.

    정확 매치(`source_type_scores`의 키와 동일) -> alias 키워드 매칭 -> `default_score`
    순으로 조회한다. 매칭되는 유형이 없다고 임의로 높은 점수를 주지 않는다.
    """
    config = config if config is not None else load_source_reliability_config()
    text = (source_type_or_name or "").strip().lower()
    scores = config["source_type_scores"]

    if text in scores:
        return scores[text]

    aliases = config.get("aliases", {})
    for key, keywords in aliases.items():
        if any(keyword.lower() in text for keyword in keywords):
            return scores[key]

    return config.get("default_score", 1)


@dataclass(frozen=True)
class ScoredFact:
    fact: str
    source: str
    score: int


def resolve_conflict(
    candidates: list[tuple[str, str]], config: dict | None = None
) -> ScoredFact:
    """[(fact, source_type_or_name), ...] 중 Source Reliability Score가 가장 높은 사실을
    선택한다. 점수가 동점이면 먼저 나온 항목을 유지한다(임의 재정렬 금지 — 결정론적 동작).
    """
    if not candidates:
        raise ValueError("candidates가 비어 있다 — 충돌 해소할 대상이 없다.")

    config = config if config is not None else load_source_reliability_config()
    scored = [
        ScoredFact(fact=fact, source=source, score=score_for_source_type(source, config))
        for fact, source in candidates
    ]
    best = scored[0]
    for item in scored[1:]:
        if item.score > best.score:
            best = item
    return best
