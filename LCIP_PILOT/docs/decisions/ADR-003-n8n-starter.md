# ADR-003 — Workflow Orchestrator로 n8n Cloud Starter 채택

- **상태**: Accepted
- **날짜**: 2026-08-05

## 맥락

수집·정규화·분류·분석·저장·발송을 모듈화하고 스케줄·재시도를 관리할 오케스트레이터가 필요하다.

## 결정

n8n Cloud Starter를 사용하고, WF-P01~P10 + WF-P99의 11개 모듈형 Sub-workflow로 구성한다.

## 이유

- 코드 없이/적은 코드로 스케줄·HTTP·Google 연동 가능
- Cloud Starter 요금이 Pilot 예산(월 10만원 이하) 내에서 감당 가능
- Sub-workflow 구조로 재사용·테스트 용이

## 트레이드오프

- Starter 플랜은 실행 횟수 제한 → 워크플로우 실행 횟수 최소화, "변동 중심 운영" 원칙 적용
  (신규 중요 변화가 있을 때만 고비용 분석·알림 수행)
- Sub-workflow를 과도하게 쪼개면 실행 횟수가 늘어남 → TASK-007 규칙대로 과도한 분할 금지
