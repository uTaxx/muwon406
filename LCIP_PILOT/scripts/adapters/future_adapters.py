"""Naver/DART/정부보도자료/IR Adapter — 아직 미구현 (Round 4 확장 지점 증명용).

`config/sources.yaml`에서 SRC-0003(Naver)/SRC-0004(DART)는 `active: false`다 — API Key
준비(§24 질문 항목) 전까지는 구현하지 않는다. 정부/IR Adapter도 동일하게 확장 지점만
남겨둔다. 나중에 실제 연동이 필요해지면 scripts/pipeline/*을 전혀 건드리지 않고 이 Adapter들만
채우면 된다는 것을 보여준다 (providers/future_providers.py와 동일한 설계 원칙).

Round 6 감사 표시: `scripts/demo_pilot.py`는 이 4개 Adapter를 전혀 호출하지 않는다 —
`tests/test_adapters.py`에서만 "SourceAdapter 계약을 지키는지"를 확인한다. 삭제 후보가
아니라 Round 4가 승인한 "Adapter 교체 가능성" 증거이므로 그대로 둔다.
"""
from __future__ import annotations

from .base import RawArticle, SourceAdapter


class NaverNewsAdapter(SourceAdapter):
    """SRC-0003. Naver API Key 미준비 — 아직 구현하지 않는다."""

    def collect(self, query: str) -> list[RawArticle]:
        raise NotImplementedError(
            f"{self.source_id}: NaverNewsAdapter는 아직 구현되지 않았다 "
            "(Naver API Key 준비 필요, config/sources.yaml active=false)."
        )


class DartFilingAdapter(SourceAdapter):
    """SRC-0004. DART API Key 미준비 — 아직 구현하지 않는다."""

    def collect(self, query: str) -> list[RawArticle]:
        raise NotImplementedError(
            f"{self.source_id}: DartFilingAdapter는 아직 구현되지 않았다 "
            "(DART API Key 준비 필요, config/sources.yaml active=false)."
        )


class GovernmentPressReleaseAdapter(SourceAdapter):
    """정부 보도자료. 소스 등록 전 — 아직 구현하지 않는다."""

    def collect(self, query: str) -> list[RawArticle]:
        raise NotImplementedError(
            f"{self.source_id}: GovernmentPressReleaseAdapter는 아직 구현되지 않았다 "
            "(대상 정부기관 소스 미등록)."
        )


class IRPageAdapter(SourceAdapter):
    """상장사 IR 페이지. 소스 등록 전 — 아직 구현하지 않는다."""

    def collect(self, query: str) -> list[RawArticle]:
        raise NotImplementedError(
            f"{self.source_id}: IRPageAdapter는 아직 구현되지 않았다 (대상 IR 페이지 미등록)."
        )
