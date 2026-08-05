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

from pipeline.dashboard_feed import build_dashboard_data
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
    """StorageBackend(ARTICLE_DB/INTELLIGENCE_DB)에서 실제 Pipeline 결과를 읽어 대시보드
    입력 형태로 변환한다 (`pipeline/dashboard_feed.py` 재사용)."""

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
        )
