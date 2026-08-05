# ADR-002 — Pilot Registry/DB로 Google Sheets 채택

- **상태**: Accepted
- **날짜**: 2026-08-05

## 맥락

ARTICLE_DB, INTELLIGENCE_DB, COST_LOG 등 구조화된 레코드를 저장·조회할 DB가 필요하다.
PostgreSQL 등 별도 DB는 서버 운영비·관리 부담이 크다 (ADR-004 참고).

## 결정

단일 Master Spreadsheet에 11개 탭(CONFIG_MASTER, TOPIC_CONFIG, SOURCE_REGISTRY, ARTICLE_DB,
INTELLIGENCE_DB, SOURCE_HEALTH, COST_LOG, SENT_HISTORY, ERROR_LOG, CHANGE_REQUEST, CHANGE_LOG)를
Pilot Registry/DB로 사용한다.

## 이유

- n8n Google Sheets 노드로 append/batch update 직접 지원
- 사람이 직접 열람·필터링 가능 (전용 Admin 포털 불필요, ADR-004와 일관)
- 무료/저비용 티어로 Pilot 규모의 레코드 수 충분히 처리

## 트레이드오프

- Row 수 증가 시 성능 저하 가능 → Archive 주기적 이동 정책 필요(운영 단계 과제)
- 동시성·트랜잭션 보장 없음 → Sheet Write는 batch/append 위주로 설계, Cost Guard 등 카운터는
  단일 워크플로우에서만 갱신
