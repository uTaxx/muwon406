# TODO

> 2026-08-05 Architect Review 반영 후 갱신. TASK-008 이후 우선순위가 변경되었다 (Q5).

## 사용자가 해야 할 작업 (Claude Code가 추정/대신 수행하지 않음)

### 다음 라운드 진행 전 확인 필요 — 03_BUILD_SPECIFICATION.md §24 질문 항목

TASK-009(Claude API)부터 순서대로 진행하므로, 아래 중 Claude API 관련 항목이 가장 시급하다.

- [ ] Claude API Key 준비 여부 (Anthropic Console) — **TASK-009 착수 전 필수**
- [ ] 사용할 Claude 모델 ID 확정 — Architect Review Q3 권장: 1차 분류 **Haiku 계열**,
      심층분석 **Sonnet 계열** (`config/cost_policy.yaml`의 `classification_recommended_tier`/
      `deep_analysis_recommended_tier` 참고). 실제 모델 ID는 `.env`의
      `LCIP_CLASSIFICATION_MODEL`/`LCIP_DEEP_ANALYSIS_MODEL`에 입력
      → `config/model_pricing.yaml`의 placeholder 단가도 함께 갱신 필요
- [ ] Google OAuth 방식 선택: Desktop OAuth / Service Account / n8n Credential only
      (현재 기본값은 `n8n_only` — 로컬에서 실제 쓰기 없음) — TASK-008(마지막 순위)에서 필요
- [ ] 기존 Google Drive Root Folder ID 존재 여부 확인 → 있다면 `.env`의
      `GOOGLE_DRIVE_ROOT_FOLDER_ID`에 입력
- [ ] 기존 Master Spreadsheet ID 존재 여부 확인 → 있다면 `.env`의
      `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`에 입력
- [ ] n8n Base URL / API Key 준비 여부 — TASK-008(마지막 순위)에서 필요
- [ ] Gmail OAuth 연결 계정 — TASK-013에서 필요
- [ ] Telegram Bot Token / Chat ID 준비 여부 — TASK-013에서 필요
- [ ] 테스트 수신 이메일 주소 — TASK-013에서 필요
- [ ] DART API Key 보유 여부 (Sprint 6 확장 대상)
- [ ] Google Drive Desktop 동기화 사용 여부

### Knowledge Base — 출처 필요 (우선순위 확정, Architect Review Q6)

`knowledge/KNOWLEDGE_POLICY.md` §4에 확정된 순서대로 공개 출처를 찾아 채워야 한다. 출처
확인 순서는 `knowledge/SOURCE_PRIORITY.md` 기준(공식 홈페이지 → 사업보고서 →
지속가능경영보고서 → DART → IR 자료 → 공식 보도자료 → 정부자료 → 언론 → RSS).

1. `LX_HAUSYS_COMPANY_DNA.md` — 특히 "10. Risk"의 "미국 사업 및 엔지니어드스톤 관련 노출"이
   TOP-0001 분석의 핵심 근거이므로 최우선
2. `LX_HAUSYS_VALUE_CHAIN.md`
3. `GROUP_RISK_MAP.md`
4. `GROUP_OPPORTUNITY_MAP.md`
5. `STRATEGY_PLAYBOOK.md`
6. `LX_HOLDINGS_CONTEXT.md`
7. `PLATFORM_CONSTITUTION.md` (이미 완성 — 회사 사실 아님, 낮은 우선순위)

각 항목은 `knowledge/KNOWLEDGE_POLICY.md` §3 서식(Source/Reference URL/Confidence/
Last Verified)을 따라 채운다.

## Claude Code가 다음 라운드에서 할 작업 (사용자 승인 후) — Architect Review Q5로 순서 변경

원래 TASK 번호 순서(008→009→...)가 아니라 아래 순서로 진행한다. **TASK-008(n8n 자동배포)은
실제 Workflow 로직이 완성된 뒤로 마지막 순위로 미뤄졌다** — 지금은 JSON 생성(TASK-007)까지만
유지한다.

- [ ] **TASK-009** Claude API Client & Prompts — 실제 Anthropic API 연동 (현재
      `scripts/claude_client.py`는 stub, `build_cached_messages()`로 Static/Dynamic
      Block 구조는 준비됨)
- [ ] **TASK-010** News Collection Logic — Master Pipeline의 News Collect 단계 실제 구현
- [ ] **TASK-011** Relevance & Deep Analysis — Master Pipeline의 Rule Filter/AI Analyze
      단계 실제 Claude 연동
- [ ] **TASK-012** Dashboard — Master Pipeline의 Dashboard 단계와 `build_dashboard.py`
      실데이터 연동 (Mode1 기본 유지)
- [ ] **TASK-013** Gmail & Telegram — Master Pipeline의 Notification 단계 실제 발송 연동
      (test_mode 유지)
- [ ] **TASK-008** n8n API Deployment Tooling (마지막) — 위 항목이 전부 완성된 뒤 실제 n8n
      REST API 자동배포 연동
- [ ] TASK-014 Source Health — WF-P02와 `scripts/source_health_check.py` 연동
- [ ] TASK-015 Cost Guard — WF-P03과 `scripts/cost_guard.py` 연동, 실제 COST_LOG 연결
- [ ] TASK-016 Natural Language Admin — WF-P04 실제 Claude 연동
- [ ] TASK-017 Integration Test
- [ ] TASK-018 Pilot Deployment

## 이번 라운드(Architect Review 반영)에서 알려진 한계

- Google Drive/Sheets/n8n/이메일/Telegram/Anthropic API 어떤 것도 실제로 연결·호출되지
  않았다.
- `knowledge/*.md`는 16계층 Taxonomy 구조로 재구성되었으나 여전히 전부 TODO 상태이며, 실제
  회사 사실 리서치는 아직 수행하지 않았다.
- n8n 워크플로우는 5개(Master Pipeline 포함)로 통합된 구조(노드/연결/Trigger/Error 분기)만
  갖췄고, Code 노드 내부 로직은 TODO 주석으로 남아 있다 (TASK-009~013에서 구현).
- Prompt Caching 구조(Static/Dynamic Block)는 `prompts/*.md`와
  `scripts/claude_client.py:build_cached_messages()`에 준비되었으나, 실제 Anthropic API
  호출로 검증되지는 않았다 (TASK-009에서 검증).
