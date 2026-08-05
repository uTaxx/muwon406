# TODO

## 사용자가 해야 할 작업 (Claude Code가 추정/대신 수행하지 않음)

### 다음 라운드(TASK-008 이후) 진행 전 확인 필요 — 03_BUILD_SPECIFICATION.md §24 질문 항목

- [ ] Google OAuth 방식 선택: Desktop OAuth / Service Account / n8n Credential only
      (현재 기본값은 `n8n_only` — 로컬에서 실제 쓰기 없음)
- [ ] 기존 Google Drive Root Folder ID 존재 여부 확인 → 있다면 `.env`의
      `GOOGLE_DRIVE_ROOT_FOLDER_ID`에 입력
- [ ] 기존 Master Spreadsheet ID 존재 여부 확인 → 있다면 `.env`의
      `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`에 입력
- [ ] n8n Base URL / API Key 준비 여부
- [ ] n8n API 자동배포 사용 여부, 또는 n8n UI에서 수동 Import 여부
- [ ] Claude API Key 준비 여부 (Anthropic Console)
- [ ] 사용할 Claude 모델명 확정 (1차 분류용 저비용 모델 / 심층분석용 Sonnet급 모델)
      → `config/model_pricing.yaml`의 placeholder 단가도 함께 갱신 필요
- [ ] Gmail OAuth 연결 계정
- [ ] Telegram Bot Token / Chat ID 준비 여부
- [ ] 테스트 수신 이메일 주소
- [ ] DART API Key 보유 여부 (Sprint 6 확장 대상)
- [ ] Google Drive Desktop 동기화 사용 여부

### Google Sheets — 초안(draft) 상태 탭 검토 필요

`SENT_HISTORY`, `ERROR_LOG`, `CHANGE_REQUEST`, `CHANGE_LOG` 4개 탭은 원본 설계문서에 컬럼이
명문화되어 있지 않아 이번 라운드에서 문맥상 합리적으로 초안 작성했다
(`docs/04_DATA_AND_CONFIG_SCHEMA.md` §3, `config/sheet_structure.yaml`). 실제 Google Sheets
생성 전 컬럼 구성을 검토해달라.

### Knowledge Base — 출처 필요

`knowledge/*.md` 7개 문서의 `TODO: source required` 항목은 전부 공개 출처(DART, IR, 공식
홈페이지, 지속가능경영보고서) 확인 후 채워야 한다. 특히
`knowledge/LX_HAUSYS_COMPANY_DNA.md`의 "9. 미국 사업 및 엔지니어드스톤 관련 노출"은 TOP-0001
리스크 분석의 핵심 근거이므로 우선순위가 높다.

## Claude Code가 다음 라운드에서 할 작업 (사용자 승인 후)

- [ ] TASK-008 n8n API Deployment Tooling — 실제 n8n REST API 연동
- [ ] TASK-009 Claude API Client & Prompts — 실제 Anthropic API 연동 (현재 `scripts/claude_client.py`는 stub)
- [ ] TASK-010 News Collection Logic — 실제 RSS 수집 파이프라인
- [ ] TASK-011 Relevance & Deep Analysis — 실제 Claude 호출 연동
- [ ] TASK-012 Dashboard — WF-P06과 `build_dashboard.py` 실데이터 연동
- [ ] TASK-013 Gmail & Telegram — 실제 발송 연동 (test_mode 유지)
- [ ] TASK-014 Source Health — n8n WF-P08과 `scripts/source_health_check.py` 연동
- [ ] TASK-015 Cost Guard — n8n WF-P09과 `scripts/cost_guard.py` 연동, 실제 COST_LOG 연결
- [ ] TASK-016 Natural Language Admin — WF-P10 실제 Claude 연동
- [ ] TASK-017 Integration Test
- [ ] TASK-018 Pilot Deployment

## 이번 라운드에서 알려진 한계 (의도된 범위 제한)

- Google Drive/Sheets/n8n/이메일/Telegram 어떤 것도 실제로 생성·배포·발송되지 않았다.
- `knowledge/*.md`는 전부 템플릿 상태이며 실제 회사 사실이 채워져 있지 않다.
- n8n 워크플로우는 구조(노드/연결/Trigger/Error 분기)만 갖췄고, Code 노드 내부 로직은
  TODO 주석으로 남아 있다 (Sprint 2+에서 구현).
