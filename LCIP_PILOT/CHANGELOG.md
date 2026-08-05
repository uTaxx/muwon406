# Changelog

모든 주요 변경사항을 이 파일에 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/)를
느슨하게 따른다.

## [Unreleased]

### Changed — Architect Review 반영 (2026-08-05, 2차)

ChatGPT Architect Review(Q1~Q7) 승인 및 지시 반영. TASK-008 이전 정리 라운드. 외부 API
호출 없음.

- **Q1 (ADR-006)**: 문서 우선순위 고정 — `docs/decisions/ADR-006-document-priority-policy.md`
  신규 작성. 충돌 시 BUILD_SPECIFICATION → SYSTEM_BLUEPRINT → DEVELOPMENT_MANUAL →
  HANDOVER 순.
- **Q2**: `SENT_HISTORY`(+workflow_id/topic_id/subject/content_hash/delivery_latency_ms),
  `ERROR_LOG`(+severity/retry_count/stack_trace/first_occurred/last_occurred),
  `CHANGE_REQUEST`(+request_source/requested_by/approved_by/approved_at/implemented_at),
  `CHANGE_LOG`(+change_summary/rollback_version/implemented_by) 컬럼 확장,
  `config/sheet_structure.yaml` 4개 탭 draft→confirmed. `schemas/change_request.schema.json`
  동기화.
- **Q3**: `config/cost_policy.yaml`에 모델 tier 권장값(Haiku/Sonnet) 및 Prompt Cache 설정
  추가. `prompts/*.md` 6개 전부 Static Block(캐시 대상)/Dynamic Block(요청별) 구조로
  재작성. `scripts/claude_client.py`에 `split_prompt_blocks()`/`build_cached_messages()`
  추가. `schemas/intelligence.schema.json`/`claude_output.schema.json`에
  `mission_subcategory` 필드 추가.
- **Q4 (ADR-007)**: n8n 워크플로우 11개 → 5개로 통합 —
  `n8n/workflows/WF-P01-master-pipeline.json`(舊 WF-P01~P07 통합),
  `WF-P02-source-health.json`(舊 WF-P08), `WF-P03-cost-guard.json`(舊 WF-P09),
  `WF-P04-natural-language-admin.json`(舊 WF-P10), `WF-P99-error-handler.json`(유지).
  `config/workflow_registry.yaml` 재작성, `tests/test_n8n_json.py` 갱신.
- **Q5**: TASK 우선순위 변경 — TASK-009(Claude API)→010→011→012→013→TASK-008(n8n 자동배포,
  마지막). `TODO.md`/`CLAUDE.md` 반영.
- **Q6**: Knowledge 파일 우선순위(COMPANY_DNA→VALUE_CHAIN→RISK_MAP→OPPORTUNITY_MAP→
  STRATEGY_PLAYBOOK→HOLDINGS_CONTEXT→PLATFORM_CONSTITUTION) 및 출처 우선순위(공식 홈페이지→
  사업보고서→지속가능보고서→DART→IR→보도자료→정부자료→언론→RSS) 확정,
  `knowledge/KNOWLEDGE_POLICY.md`/`SOURCE_PRIORITY.md`에 반영.
- **Q7**: `scripts/build_dashboard.py`에 Mode1(single, 기본)/Mode2(split: HTML+CSS+JS
  분리) 지원 추가. `tests/test_dashboard.py`에 검증 테스트 4건 추가.
- **TASK-004A (신규) Knowledge Foundation Builder**: `knowledge/KNOWLEDGE_POLICY.md`의
  16계층 Taxonomy(Company→...→Last Verified)로 `LX_HAUSYS_COMPANY_DNA.md`,
  `LX_HOLDINGS_CONTEXT.md` 전면 재작성. `LX_HAUSYS_VALUE_CHAIN.md`,`GROUP_RISK_MAP.md`,
  `GROUP_OPPORTUNITY_MAP.md`,`STRATEGY_PLAYBOOK.md`,`PLATFORM_CONSTITUTION.md`는 신규
  Framework 문서 참조 및 워크플로우 명칭 갱신.
- **TASK-004B (신규) Corporate Intelligence Framework**: `knowledge/ANALYSIS_FRAMEWORK.md`,
  `INVESTMENT_FRAMEWORK.md`, `SOURCE_PRIORITY.md`, `KNOWLEDGE_POLICY.md`,
  `MISSION_FRAMEWORK.md` 5개 신규 문서 작성. 미래준비(`ma`/`carve_out`/`bolt_on`/`jv`/
  `venture`/`capital_market`/`technology`/`new_business`)와 리스크관리(`product_liability`/
  `environmental`/`safety`/`fx`/`raw_material`/`supply_chain`/`regulatory`/`litigation`/
  `policy`/`esg`) 2축·18개 서브카테고리 정의.
- 테스트: `tests/test_claude_client.py` 신규(8건), `tests/test_dashboard.py` 4건 추가,
  `tests/test_n8n_json.py` EXPECTED_FILES 갱신. 총 57개 테스트 전부 PASS.
- 문서: `CLAUDE.md`(문서/지식 우선순위, TASK 순서, n8n 원칙 갱신),
  `docs/04_DATA_AND_CONFIG_SCHEMA.md`(§5 Architect Review 반영사항 추가),
  `docs/05_ACCEPTANCE_TESTS.md`(TASK-004A/004B 완료조건, TASK-007 5개 파일로 수정).

### Added — TASK-001 ~ TASK-007 (2026-08-05)

- **TASK-001 Project Scaffold**: `LCIP_PILOT/` 전체 디렉터리 구조, `CLAUDE.md`, `README.md`,
  `.gitignore`, `.env.example`, `requirements.txt` 생성.
- **TASK-002 Core Configuration**: `config/*.yaml` 8개 파일 + `config/model_pricing.yaml`
  (Cost Guard 보조) 생성.
- **TASK-003 Data Schemas**: `schemas/*.schema.json` 6개 파일 생성 (JSON Schema Draft 2020-12).
- **TASK-004 Knowledge Templates**: `knowledge/*.md` 7개 템플릿 생성 (임의 사실 없이
  `TODO: source required` placeholder만 포함).
- **TASK-005 Google Drive Tooling**: `scripts/create_drive_structure.py` (dry-run 기본,
  `n8n_only` 인증모드에서는 어떤 외부 API도 호출하지 않음), `docs/GOOGLE_DRIVE_SETUP.md`.
- **TASK-006 Google Sheets Tooling**: `scripts/create_google_sheets.py` (dry-run 기본),
  `docs/GOOGLE_SHEETS_SETUP.md`, `schemas/google_sheets_columns.json` (11개 탭).
- **TASK-007 n8n Workflow Scaffold**: `n8n/workflows/WF-P01~P10, WF-P99.json` 11개 파일
  (전부 `active:false`, placeholder credential, Manual/Error Trigger 포함).
- 보조: `scripts/bootstrap_project.py`, `validate_config.py`, `secret_scan.py`,
  `cost_guard.py`, `source_health_check.py`, `claude_client.py`(stub),
  `build_dashboard.py`, `n8n_deploy.py`/`n8n_backup.py`/`n8n_list_workflows.py`(dry-run),
  `prompts/*.md` 6개, `dashboard/*`(template/styles/app.js/sample_data), `tests/*` 및
  fixtures, `docs/04_DATA_AND_CONFIG_SCHEMA.md`(설계문서 충돌 로그), `docs/05_ACCEPTANCE_TESTS.md`,
  `docs/decisions/ADR-001~005`.

### Notes

- 이번 라운드는 외부 API를 전혀 호출하지 않았다 (Google Drive/Sheets 실제 생성 없음, n8n 실제
  배포 없음, 이메일/Telegram 실제 발송 없음). 모든 관련 스크립트는 `--dry-run`이 기본값이다.
- 4개 설계문서(00_INITIAL_CLAUDE_CODE_HANDOVER, 01_LCIP_Pilot_System_Blueprint,
  02_LCIP_Pilot_Development_Manual, 03_BUILD_SPECIFICATION) 간 충돌 4건을 발견해
  `docs/04_DATA_AND_CONFIG_SCHEMA.md` §1에 기록하고 명시적으로 해소했다.
