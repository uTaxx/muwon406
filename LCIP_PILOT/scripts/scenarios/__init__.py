"""Pilot Scenarios — Architect Review Round 7.

Round 6까지의 "하나의 통합 데모"(`scripts/demo_pilot.py`) 개념을 Round 7 지시에 따라
"5개 독립 실행 가능 Scenario"로 전환했다. 각 Scenario는 `scripts/pipeline/*`,
`scripts/providers/*`, `scripts/quick_company_scan.py`, `scripts/investment_review.py`
등 기존 컴포넌트만 재사용하며, 새 Engine을 추가하지 않는다.

- Scenario 1: 뉴스 분석(`scenario_1_news_analysis.py`)
- Scenario 2: Quick Company Scan(`scenario_2_quick_company_scan.py`)
- Scenario 3: Investment Review(`scenario_3_investment_review.py`, Scenario 2를 내부
  호출해 단독 실행 가능하게 한다)
- Scenario 4: 정부 정책 영향 분석(`scenario_4_policy_impact.py`,
  `AIProvider.analyze_policy_impact()` 신규 메서드 사용)
- Scenario 5: 경쟁사 변화 감지(`scenario_5_competitor_change_detection.py`)

각 파일은 `run(...)`(테스트/재사용용)과 `python3 scripts/scenarios/<file>.py`
(콘솔 데모용) 두 진입점을 갖는다.
"""
