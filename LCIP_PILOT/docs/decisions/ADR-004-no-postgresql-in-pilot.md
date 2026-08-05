# ADR-004 — Pilot 단계에서 PostgreSQL·전용 서버 미사용

- **상태**: Accepted
- **날짜**: 2026-08-05

## 맥락

Enterprise급 Corporate Intelligence 시스템이라면 별도 DB와 관리자 웹 포털을 갖추는 것이
일반적이다. 그러나 이 프로젝트는 "회사 정식 시스템이 아니라 실제 업무 유용성을 검증하는 최소
기능 제품(Pilot)"이다.

## 결정

Pilot 단계에서는 PostgreSQL 등 별도 DB, 전용 서버, 전용 관리자 웹 포털, 다중 사용자 권한/SSO를
구축하지 않는다. Google Sheets(ADR-002) + Google Drive(ADR-001) + n8n(ADR-003) 조합으로
동일한 기능을 구현한다.

## 이유

- 서버 운영비·유지보수 부담이 월 10만원 예산 제약과 충돌
- 1인 사용자 규모에서는 Sheets/Drive로 충분히 감당 가능
- 조기에 무거운 인프라를 들이면 "Pilot이 실제로 유용한가"라는 핵심 질문 검증이 늦어짐

## 트레이드오프

- 레코드 수·동시 사용자가 늘어나면 확장성 한계 도달 → §12 "Enterprise 전환 조건" 충족 시
  재평가 (Pilot 2~3개월 운영 후 비용 대비 효용 확인)
- 복잡한 관계형 쿼리·트랜잭션 불가 → 분석은 n8n Code 노드 + Claude API로 대체
