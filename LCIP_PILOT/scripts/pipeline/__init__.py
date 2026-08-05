"""LCIP Pilot Analysis Pipeline — Collect → Normalize → Rule Filter → Classify →
Knowledge Retrieve → Analyze → Validate → Generate Intelligence → Store.

각 단계는 독립된 순수 함수(또는 Provider/Adapter 인터페이스에만 의존하는 얇은 wrapper)로
분리되어 있다 (Round 4 지시: "Pipeline 구조는 Collect→Normalize→Classify→Knowledge
Retrieve→Analyze→Validate→Generate Intelligence→Store를 분리된 함수로 구현"). 오케스트레이션
(단계를 순서대로 호출하는 것)은 `scripts/demo_mvp.py`(TASK-017) 또는 향후 n8n Master
Pipeline이 담당하며, 이 패키지 자체는 오케스트레이터를 포함하지 않는다.
"""
