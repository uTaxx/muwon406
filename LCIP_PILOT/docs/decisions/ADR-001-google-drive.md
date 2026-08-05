# ADR-001 — Primary Storage로 Google Drive 채택

- **상태**: Accepted
- **날짜**: 2026-08-05

## 맥락

Pilot은 Knowledge Base 원문, 대시보드 HTML, 아카이브를 저장할 곳이 필요하다. 별도 서버·오브젝트
스토리지를 두면 운영비와 관리 부담이 늘어난다.

## 결정

Google Drive를 Primary Storage로 사용한다. `LCIP_PILOT/` 폴더 트리(`00_Project/ ~ 06_Admin/`,
TASK-005 기준)에 Knowledge, Data 참조, Dashboard, Reports, Archive를 분리 저장한다.

## 이유

- 이미 보유한 Google Workspace 구독으로 추가 비용 없음
- n8n Google Drive 노드로 바로 연동 가능
- 사람이 직접 열람·수정하기 쉬움 (Markdown/HTML)

## 트레이드오프

- 대용량 구조화 쿼리에는 부적합 → 구조화 데이터는 Google Sheets(ADR-002)로 분리
- 동시쓰기 충돌 가능성 → CURRENT/ARCHIVE 분리, 쓰기는 n8n 워크플로우로 단일화
