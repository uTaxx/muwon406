# TODO

> 2026-08-05 Architect Review Round 3 반영 후 갱신. TASK-004C/004D/004E(Knowledge Layer)
> 완료 — 이제 TASK-009(Claude API)가 다음 순서다.

## 사용자가 해야 할 작업 (Claude Code가 추정/대신 수행하지 않음)

### 다음 라운드 진행 전 확인 필요 — 03_BUILD_SPECIFICATION.md §24 질문 항목

TASK-009(Claude API)부터 순서대로 진행하므로, 아래 중 Claude API 관련 항목이 가장 시급하다.

- [ ] Claude API Key 준비 여부 (Anthropic Console) — **TASK-009 착수 전 필수**
- [ ] 사용할 Claude 모델 ID 3종 확정 — `config/model_registry.yaml`에서 관리 (Architect
      Review Round 3 Q4):
      - 1차 분류(`classification`, Haiku 계열) → `.env`의 `LCIP_CLASSIFICATION_MODEL`
      - 심층분석(`deep_analysis`, Sonnet 계열) → `.env`의 `LCIP_DEEP_ANALYSIS_MODEL`
      - 미래준비/Quick Company Scan(`future`, Opus 계열) → `.env`의
        `LCIP_FUTURE_READINESS_MODEL`
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

### Knowledge Base — 출처 필요 (우선순위 확정, Architect Review Round 2 Q6)

`knowledge/KNOWLEDGE_POLICY.md` §4에 확정된 순서대로 공개 출처를 찾아 채워야 한다. 출처
확인 순서는 `knowledge/SOURCE_PRIORITY.md` 기준(공식 홈페이지 → 사업보고서 →
지속가능경영보고서 → DART → IR 자료 → 공식 보도자료 → 정부자료 → 언론 → RSS). 진행 상황은
`python scripts/knowledge_quality.py --verbose`로 정량 확인 가능 (Quality Score).

1. `LX_HAUSYS_COMPANY_DNA.md` — 특히 "10. Risk"의 "미국 사업 및 엔지니어드스톤 관련 노출"이
   TOP-0001 분석의 핵심 근거이므로 최우선 (현재 Quality Score 0%)
2. `LX_HAUSYS_VALUE_CHAIN.md`
3. `GROUP_RISK_MAP.md`
4. `GROUP_OPPORTUNITY_MAP.md`
5. `STRATEGY_PLAYBOOK.md`
6. `LX_HOLDINGS_CONTEXT.md` (현재 Quality Score 50% — N/A 계층 6개가 이미 "신뢰가능"으로
   카운트되기 때문. 실제로 채워야 할 계층은 6개: Company/Business/Government/Risk/
   Opportunity/Investment Point)
7. `PLATFORM_CONSTITUTION.md` (이미 완성 — 회사 사실 아님, 낮은 우선순위)

각 항목은 `knowledge/KNOWLEDGE_POLICY.md` §3 서식(Source/Reference URL/Confidence/
Last Verified)을 따라 채운다.

## Claude Code가 다음에 할 작업 (사용자 승인 후) — Architect Review Round 2 Q5 / Round 3 순서

원래 TASK 번호 순서가 아니라 아래 순서로 진행한다.

- [x] **TASK-004A** Knowledge Foundation Builder — 완료
- [x] **TASK-004B** Corporate Intelligence Framework — 완료
- [x] **TASK-004C** Knowledge Governance — 완료 (`knowledge/KNOWLEDGE_GOVERNANCE.md`,
      `scripts/knowledge_quality.py`)
- [x] **TASK-004D** Quick Company Scan Framework — 완료
      (`knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`, `schemas/quick_company_scan.schema.json`,
      `prompts/quick_scan.md` 확장)
- [x] **TASK-004E** Corporate Intelligence Taxonomy — 완료
      (`knowledge/INTELLIGENCE_TAXONOMY.md`, `intelligence_categories` 필드 스키마 반영)
- [ ] **TASK-009** Claude API Client & Prompts (다음 순서) — 실제 Anthropic API 연동 (현재
      `scripts/claude_client.py`는 stub, `build_cached_messages()`/`get_model_name()`으로
      Static/Dynamic Block 구조와 Model Registry 조회 로직은 준비됨)
- [ ] **TASK-010** News Collection Logic — Master Pipeline의 News Collect 단계 실제 구현
- [ ] **TASK-011** Relevance & Deep Analysis — Master Pipeline의 Rule Filter/AI Analyze
      단계 실제 Claude 연동
- [ ] **TASK-012** Dashboard — Master Pipeline의 Dashboard 단계와 `build_dashboard.py`
      실데이터 연동 (Mode1 기본 유지)
- [ ] **TASK-013** Gmail & Telegram — Master Pipeline의 Notification 단계 실제 발송 연동
      (test_mode 유지)
- [ ] **TASK-008** n8n API Deployment Tooling (마지막) — 위 항목이 전부 완성된 뒤 실제 n8n
      REST API 자동배포 연동
- [ ] TASK-014 Source Health — WF-P08과 `scripts/source_health_check.py` 연동
- [ ] TASK-015 Cost Guard — WF-P09과 `scripts/cost_guard.py` 연동, 실제 COST_LOG 연결
- [ ] TASK-016 Natural Language Admin — WF-P10 실제 Claude 연동
- [ ] TASK-017 Integration Test
- [ ] TASK-018 Pilot Deployment

## 이번 라운드(Architect Review Round 3 반영)에서 알려진 한계

- Google Drive/Sheets/n8n/이메일/Telegram/Anthropic API 어떤 것도 실제로 연결·호출되지
  않았다.
- `knowledge/*.md`는 16계층 Taxonomy 구조로 재구성되었으나 여전히 대부분 TODO 상태이며,
  실제 회사 사실 리서치는 아직 수행하지 않았다 (`LX_HOLDINGS_CONTEXT.md`의 N/A 계층 6개만
  구조상 "완료" 취급).
- n8n 워크플로우는 5개(Master Pipeline 포함, ID는 WF-P01/08/09/10/99 — ADR-008에 따라
  원래 번호 유지)로 통합된 구조(노드/연결/Trigger/Error 분기)만 갖췄고, Code 노드 내부 로직은
  TODO 주석으로 남아 있다 (TASK-009~013에서 구현).
- `config/model_registry.yaml`의 모든 `model_id`가 아직 `null`이다 — 실제 Anthropic 모델 ID
  확정 전까지 `get_model_name()` 호출 시 명시적으로 에러가 난다 (의도된 동작, 임의 모델
  추측 방지).
- Quick Company Scan(`prompts/quick_scan.md`)과 Investment Recommendation 신호는 아직
  파이프라인에 연결되지 않았다 (Sprint 6 확장 대상, 구조만 준비).
