"""Digest 조립 — 뉴스 수집 실체화 라운드(2026-08-08) 신설.

한 번의 배치 실행(`scripts/run_news_collection.py`)에서 여러 건의 (article,
intelligence) 쌍이 나올 수 있다. 사용자 요구("의미있는 기사는 임플리케이션과
제언사항을 짧게 요약하여 출력")에 따라, `importance_level`이 긴급/중요인 것만 추려
하나의 다이제스트 메시지로 합친다 — 참고 등급은 축적만 하고 알림 대상에서 제외한다
(`knowledge/STRATEGY_PLAYBOOK.md` §2와 동일한 원칙).

`config/notification.yaml`의 `email.max_highlighted_changes`를 그대로 재사용한다 —
새 설정 키를 만들지 않는다.
"""
from __future__ import annotations

from _common import load_yaml

_ALERT_LEVELS = ("긴급", "중요")


def select_digest_records(records: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    """(article, intelligence) 쌍 중 importance_level이 긴급/중요인 것만 남긴다.

    긴급이 먼저, 그다음 중요 순으로 정렬한다(같은 등급 내에서는 원래 순서 유지).
    """
    alert_records = [
        (article, intelligence)
        for article, intelligence in records
        if intelligence.get("importance_level") in _ALERT_LEVELS
    ]
    return sorted(alert_records, key=lambda pair: _ALERT_LEVELS.index(pair[1]["importance_level"]))


def build_digest_body(records: list[tuple[dict, dict]]) -> str:
    """다이제스트 본문(한국어, 카드형 요약)을 만든다. `records`는 이미
    `select_digest_records()`로 필터링된 것을 기대한다."""
    notification_config = load_yaml("config/notification.yaml")
    max_items = notification_config["email"]["max_highlighted_changes"]

    if not records:
        return "오늘 새로 발송할 만큼 중요한 변화는 없다."

    lines = [f"오늘의 핵심 변화 {min(len(records), max_items)}건:"]
    for article, intelligence in records[:max_items]:
        title = article.get("title_original", "(제목 없음)")
        level = intelligence.get("importance_level", "")
        implications = "; ".join(intelligence.get("lx_impact", [])) or "(LX 영향 근거 없음)"
        actions = "; ".join(intelligence.get("recommended_actions", [])) or "(제언 없음)"
        lines.append(f"\n[{level}] {title}\n- 시사점: {implications}\n- 제언: {actions}")

    remaining = len(records) - max_items
    if remaining > 0:
        lines.append(f"\n(그 외 {remaining}건은 대시보드에서 확인)")

    return "\n".join(lines)


def build_digest_subject(records: list[tuple[dict, dict]]) -> str:
    notification_config = load_yaml("config/notification.yaml")
    base_subject = notification_config["email"]["subject"]
    if not records:
        return f"{base_subject} — 신규 주요 변화 없음"
    return f"{base_subject} — 신규 {len(records)}건"
