"""TASK-012A — Dashboard Data Provider.

Round 5 구조: **Data Provider → Widget → Dashboard**. Widget(`dashboard_widgets.py`)이
소비하는 `data: dict`가 어디서 오는지를 추상화한 것이 이 계층이다 — 정적 JSON 파일에서
올 수도 있고(데모/오프라인), 실제 Pipeline이 `StorageBackend`에 쌓은 ARTICLE_DB/
INTELLIGENCE_DB에서 올 수도 있다. Widget/Dashboard 쪽 코드는 어느 Provider를 쓰든
수정하지 않는다.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from _common import load_yaml
from pipeline.dashboard_feed import build_dashboard_data
from reference_library import reference_library_summary
from storage.base import StorageBackend


class DashboardDataProvider(ABC):
    """모든 Dashboard Data Provider가 구현해야 하는 계약."""

    @abstractmethod
    def get_data(self) -> dict:
        """Widget들이 소비할 dashboard 입력 데이터(dict)를 반환한다."""


class StaticJSONDataProvider(DashboardDataProvider):
    """고정 JSON 파일(예: dashboard/sample_data.json)을 그대로 공급한다 — 데모/오프라인/
    테스트용 기본 구현."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def get_data(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))


class PipelineDashboardDataProvider(DashboardDataProvider):
    """StorageBackend(ARTICLE_DB/INTELLIGENCE_DB/COMPANY_SCAN_DB)와 Source Registry에서
    실제 Pipeline 결과를 읽어 Executive Dashboard 입력 형태로 변환한다
    (`pipeline/dashboard_feed.py` 재사용). Round 8부터 Quick Company Scan/Investment
    Review/Source Health 3개 Widget이 추가되어 COMPANY_SCAN_DB와
    `config/sources.yaml`도 함께 읽는다 — `storage`가 COMPANY_SCAN_DB 컬렉션을 아직
    갖고 있지 않아도(예: Scenario 1만 실행한 경우) `load_all()`은 빈 리스트를 반환하므로
    에러 없이 동작한다.

    Round 12 TASK 2 — Home Dashboard "Reference Library" 카드용으로
    `reference_library.reference_library_summary()`도 함께 조회해 넘긴다. 이 클래스가
    유일하게 실제 파일시스템(reference_library/)을 읽는 지점이다 —
    `pipeline/dashboard_feed.py`와 `build_dashboard.py`는 전달받은 값만 그대로
    가공/렌더링한다(계층 분리, 테스트 격리 유지).
    """

    def __init__(self, storage: StorageBackend, topic_display_name: str, generated_at_kst: str):
        self.storage = storage
        self.topic_display_name = topic_display_name
        self.generated_at_kst = generated_at_kst

    def get_data(self) -> dict:
        return build_dashboard_data(
            topic_display_name=self.topic_display_name,
            generated_at_kst=self.generated_at_kst,
            articles=self.storage.load_all("ARTICLE_DB"),
            intelligences=self.storage.load_all("INTELLIGENCE_DB"),
            company_scans=self.storage.load_all("COMPANY_SCAN_DB"),
            sources=load_yaml("config/sources.yaml")["sources"],
            reference_library_summary=reference_library_summary(),
        )
