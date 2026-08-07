"""FinancialDataProvider — Architect Review Round 8, Quick Company Scan 파이프라인의
"Financial Provider" 단계.

Round 5부터 `scenarios/scenario_3_investment_review.py`(구 `demo_quick_scan.py`)에
`DEMO_PEERS`라는 이름으로 하드코딩되어 있던 Comparable Peer 목록을 Provider Layer
패턴(추상 클래스 + Mock 구현체)으로 옮긴 것이다 — 새 Framework가 아니라 기존
`providers/`의 "추상 인터페이스 + Mock" 패턴을 재무 데이터에도 적용한 것뿐이다
(ADR-010 "새 Framework 금지" 원칙 참고).

Round 10 지시("Peer를 회사별 실제 Peer로 변경한다. 현재 'Peer A/Peer B' 삭제. Mock
데이터여도 회사별 Peer는 실제 회사여야 한다")에 따라, 회사와 무관하게 항상 동일한
"Peer A/B (예시)"를 반환하던 Round 8 설계를 뒤집는다. Comparable Peer의 **회사명은
실제 회사**(`config/company_registry.yaml`에 이미 등록된 업종 인접 기업)이고,
**배수(EV/EBITDA·PER·PBR)는 WebSearch로 실제 확인된 값만** 채운다 — 비상장이거나
확인하지 못한 값은 임의로 추정하지 않고 `None`으로 정직하게 남긴다
(`investment_review.py:_avg()`가 이미 `None`을 제외하고 평균을 계산하므로 그대로
동작한다). 실제 재무 데이터 소스(Bloomberg/CapitalIQ/공시 XBRL 등) 연동 자체는 여전히
RC2 이후 범위다 — 이번 변경은 "Peer가 누구인지"를 정직하게 만드는 것이지, 실시간
재무 API를 연동하는 것이 아니다(Architect Review Round 8/10 "Financial Provider는
Mock 유지" 지시와 계속 일치한다).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from _common import load_yaml
from investment_review import ComparablePeer


class FinancialDataProvider(ABC):
    """모든 재무 데이터 공급자가 구현해야 하는 계약."""

    @abstractmethod
    def get_comparable_peers(self, company_id: str | None) -> list[ComparablePeer]:
        """company_id에 대한 Comparable Peer(EV/EBITDA·PER·PBR) 목록을 반환한다."""


# 회사별 Comparable Peer 그룹(업종 인접 실제 회사, Round 10 리서치 기준). LX Hausys는
# Architect가 직접 예시로 지정한 5개사(KCC/Hanssem/LIXIL/YKK AP/Saint-Gobain)를 그대로
# 쓴다. 나머지는 같은 업종(엔지니어드스톤·건축자재·창호) 안에서 실제로 비교 가능한
# 회사를 골랐다 — Company Registry에 없는 회사를 새로 지어내지 않는다.
_PEER_COMPANY_IDS: dict[str, list[str]] = {
    "LX_HAUSYS": ["KCC", "HANSSEM", "LIXIL", "YKK_AP", "SAINT_GOBAIN"],
    "KCC": ["LX_HAUSYS", "HANSSEM", "SAINT_GOBAIN"],
    "HANSSEM": ["LX_HAUSYS", "KCC"],
    "CAESARSTONE": ["COSENTINO", "LX_HAUSYS"],
    "COSENTINO": ["CAESARSTONE", "LX_HAUSYS"],
    "SHAW_INDUSTRIES": ["SAINT_GOBAIN", "LIXIL"],
    "LIXIL": ["SAINT_GOBAIN", "LX_HAUSYS", "YKK_AP"],
    "YKK_AP": ["SCHUCO", "LIXIL"],
    "SCHUCO": ["YKK_AP", "LIXIL"],
    "SAINT_GOBAIN": ["LIXIL", "LX_HAUSYS", "KCC"],
}

# TOP10 외 회사(아직 Knowledge Population 대상이 아닌 나머지 20개사)를 스캔할 경우의
# 기본 Peer 그룹 — TOP-0001(엔지니어드스톤·건축자재) 업종 내 대표 상장사 2곳을 쓴다.
# "회사별 실제 Peer" 원칙은 지키되(가짜 이름 아님), 업종 인접성은 LX Hausys 그룹만큼
# 정밀하지 않다는 점을 감안한 최소한의 기본값이다.
_DEFAULT_PEER_COMPANY_IDS: list[str] = ["LX_HAUSYS", "SAINT_GOBAIN"]

# 실제 WebSearch로 확인된 배수(Round 10, 2026-08-07 기준). 확인하지 못한 값(비상장 등)은
# 키 자체를 넣지 않는다 — ComparablePeer 필드가 `float | None`이라 없는 값은 그대로
# None이 되고, `investment_review.py:_avg()`가 이를 평균 계산에서 자동 제외한다.
_KNOWN_MULTIPLES: dict[str, dict[str, float]] = {
    "KCC": {"per": 2.6},
    "HANSSEM": {"per": 19.88},
    "LIXIL": {"per": 41.6, "pbr": 0.76},
    "SAINT_GOBAIN": {"ev_ebitda": 6.6, "per": 12.75, "pbr": 1.8},
}

# 배수를 실제로 확인한 출처. 배수를 확인하지 못한 회사는 Company Registry의
# official_website를 참고 링크로 대신 쓴다(아래 _peer_for에서 처리).
_MULTIPLE_SOURCE_URLS: dict[str, str] = {
    "KCC": "https://stockanalysis.com/quote/krx/002380/company/",
    "HANSSEM": "https://stockanalysis.com/quote/krx/009240/company/",
    "LIXIL": "https://irbank.net/5938",
    "SAINT_GOBAIN": "https://multiples.vc/public-comps/saint-gobain-valuation-multiples",
}


def _load_company_lookup() -> dict[str, dict]:
    companies = load_yaml("config/company_registry.yaml")["companies"]
    return {c["company_id"]: c for c in companies}


def _peer_for(peer_id: str, company_lookup: dict[str, dict]) -> ComparablePeer:
    entry = company_lookup.get(peer_id, {})
    multiples = _KNOWN_MULTIPLES.get(peer_id, {})
    source_url = _MULTIPLE_SOURCE_URLS.get(peer_id) or entry.get("official_website") or (
        "https://example.com/no-source-available"
    )
    return ComparablePeer(
        entry.get("display_name", peer_id),
        ev_ebitda=multiples.get("ev_ebitda"),
        per=multiples.get("per"),
        pbr=multiples.get("pbr"),
        source_url=source_url,
    )


class MockFinancialDataProvider(FinancialDataProvider):
    """Pilot 기본값 — 실제 재무 데이터 API는 여전히 연동하지 않지만(RC2 이후 범위),
    회사별로 실제 업종 인접 기업을 Comparable Peer로 반환한다(Round 10)."""

    def get_comparable_peers(self, company_id: str | None) -> list[ComparablePeer]:
        peer_ids = _PEER_COMPANY_IDS.get(company_id or "", _DEFAULT_PEER_COMPANY_IDS)
        # 자기 자신은 자신의 Peer가 될 수 없다(예: SAINT_GOBAIN을 스캔했는데 기본
        # Peer 목록에 SAINT_GOBAIN 자신이 포함되는 경우를 제거).
        peer_ids = [p for p in peer_ids if p != company_id]
        company_lookup = _load_company_lookup()
        return [_peer_for(peer_id, company_lookup) for peer_id in peer_ids]
