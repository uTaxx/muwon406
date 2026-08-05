"""Rule Filter 단계 — AI 호출 없이 규칙(키워드/제외어)만으로 1차 걸러낸다.

CLAUDE.md 절대 원칙 #5("AI가 필요 없는 작업에는 AI를 사용하지 않는다")와
`prompts/relevance_filter.md`의 전제("규칙 기반 필터를 통과했지만 관련성이 애매한 기사만
Claude에 전달된다")를 코드로 구현한 것이 이 모듈이다. `config/topics.yaml`의
`include_keywords`/`exclude_keywords`를 사용한다.
"""
from __future__ import annotations


def passes_rule_filter(article: dict, topic: dict) -> bool:
    """제목에 exclude_keywords가 있으면 즉시 탈락, include_keywords가 하나라도 있으면 통과.

    include_keywords가 비어 있으면(설정 누락) 안전하게 전부 통과시켜 AI 단계로 넘긴다 —
    규칙이 없다고 기사를 임의로 버리지 않는다.
    """
    title = (article.get("title_original") or "").lower()

    exclude_keywords = [kw.lower() for kw in topic.get("exclude_keywords", [])]
    if any(kw in title for kw in exclude_keywords):
        return False

    include_keywords = [kw.lower() for kw in topic.get("include_keywords", [])]
    if not include_keywords:
        return True

    return any(kw in title for kw in include_keywords)
