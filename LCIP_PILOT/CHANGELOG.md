# Changelog

모든 주요 변경사항을 이 파일에 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/)를
느슨하게 따른다.

## [Unreleased]

### Added — Architect Review Round 4 반영 (2026-08-05, 4차)

ChatGPT Architect Review Round 4 승인 및 반영. Architecture Layer/Knowledge Layer가
Pilot에 충분하다고 판단, 방향을 "Framework Completion"에서 "Working Product Completion"
으로 전환 — 이제부터 새 Framework 문서는 추가하지 않고 ADR만 추가하며, 대신 동작하는
코드/테스트/실제 Pipeline 비중을 높인다. 외부 API 실제 호출은 여전히 시작하지 않는다
(Mock 기반으로 구조와 테스트를 먼저 완성).

- **Q1 (ADR-009)**: Workflow ID Active/Deprecated/Archived 3단계 생명주기 모델 —
  `docs/decisions/ADR-009-workflow-lifecycle-policy.md` 신규, `config/workflow_registry.yaml`
  전 워크플로우에 `lifecycle_stage` 필드 추가.
- **Q2**: `mission_category`(목적 축)와 `intelligence_categories`(도메인 축)는 독립적인
  두 축임을 재확인, `risk_analysis_output`에도 `intelligence_categories`를 필수로 승격 —
  `schemas/claude_output.schema.json`, `prompts/risk_analysis.md`, `prompts/policy_analysis.md`,
  `tests/test_schema.py` 동기화.
- **Q3**: Quick Company Scan을 Core(필수 7개: Company Overview/Business Structure/
  Product/Financial Snapshot/Competitor/LX Strategic Fit/Reference Sources)/Advanced
  (선택 13개)로 분리 — Pilot은 Core만으로 보고서 생성 가능해야 한다.
  `schemas/quick_company_scan.schema.json` 재작성, `knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`
  §1을 Core/Advanced 두 표로 재구성, `prompts/quick_scan.md`(v0.4.0, Core-only/전체 두
  출력 예시), Core-only 검증용 fixture `quick_company_scan_core_only.json` 추가.
- **TASK-009 Provider Layer (신규)**: `scripts/providers/` — `AIProvider`(추상 인터페이스)
  → `ClaudeProvider`(모델 조회·Prompt Cache 메시지 구성까지 실동작, 실제 네트워크 호출
  직전에서 `NotImplementedError`로 명시적으로 멈춤, `enabled=False` 기본값) /
  `MockProvider`(결정론적 mock, Pipeline 기본값) / `OpenAIProvider`·`GeminiProvider`
  (미래 확장 stub). Pipeline은 `AIProvider` 인터페이스에만 의존해 모델/공급자 교체 시
  Business Logic을 수정하지 않는다. `tests/test_providers.py`(14건).
- **TASK-010 Source Adapter (신규)**: `scripts/adapters/` — `SourceAdapter`(추상) →
  `GoogleRSSAdapter`(RSS XML 파싱은 실동작, 실제 HTTP 호출은 `http_get` 함수 주입 구조로
  실제 네트워크 없이 fixture로 테스트, `enabled=False` 기본값) / Naver/DART/정부/IR은
  `NotImplementedError` stub(API Key·소스 미등록). `tests/test_adapters.py`(9건),
  `tests/fixtures/sample_google_news_rss.xml` 추가.
- **TASK-011 Analysis Pipeline (신규)**: `scripts/pipeline/` — Collect→Normalize→Rule
  Filter→Classify→Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store를
  분리된 순수 함수로 구현. `ids.py`(ART-/INT- ID 발급), `normalize.py`(Article 스키마
  매핑·중복 판정), `rule_filter.py`(AI 호출 없는 키워드 필터), `knowledge_retrieve.py`
  (Knowledge 파일 우선순위대로 발췌+버전 추적), `generate_intelligence.py`(risk_analysis_
  output→Intelligence 레코드 매핑, 사실/해석/추론 구분), `store.py`(로컬 JSONL — Google
  Sheets 실연동 전 dry-run 스탠드인), `dashboard_feed.py`(Store→Dashboard 연결).
  `tests/test_pipeline.py`(14건).
- **TASK-012 Dashboard Widget (신규)**: `scripts/dashboard_widgets.py` — Today's
  Change/Risk Tracker/Litigation/Regulation(재사용 가능한 단일 클래스, 미국 주별·글로벌·
  세이프가드 세 구역에 인스턴스 3개)/**Statistics(신규)**/Timeline을 독립 `Widget`
  클래스로 분리. `build_dashboard.py`는 `DEFAULT_WIDGETS` 목록을 조합해 토큰을 채우도록
  리팩터링(기존 함수/토큰 하위호환 유지, 전체 테스트 무변경 통과). `dashboard/template.html`에
  "통계 요약" 섹션, `dashboard/styles.css`에 `.lcip-stat-grid` 스타일 추가.
  `tests/test_dashboard_widgets.py`(10건).
- **TASK-013/014/015 Notifier/Source Health/Cost Guard 연동 (신규)**:
  `scripts/notifiers.py`(Email/Telegram, `test_mode` dry-run, 실제 발송 경로는
  명시적으로 차단), `scripts/health_tracking.py`(`SourceAdapter.collect()` 실제 호출
  결과를 `source_health_check.py` 판정 로직에 연결), `scripts/cost_tracking.py`
  (`ProviderUsage`를 `config/model_pricing.yaml` 단가로 환산해 `cost_guard.evaluate()`와
  연결 — 단가가 아직 TODO placeholder라 실제 비용은 항상 0). 통합
  `tests/test_notifiers.py`(8건), `tests/test_health_tracking.py`(4건),
  `tests/test_cost_tracking.py`(6건).
- **TASK-017 Pilot MVP 통합 테스트 + 데모 (신규)**: `tests/test_mvp_integration.py`가
  Round 4가 정의한 Pilot MVP 성공 기준(Google RSS→1건 수집→Rule Filter→Claude 분석
  (Mock)→INTELLIGENCE_DB 저장→Dashboard 반영→Test Email→Test Telegram)을 그대로
  end-to-end 검증(1건). 전략팀 데모용 `scripts/demo_mvp.py` CLI 추가 — 동일 흐름을
  10단계로 콘솔에 출력하며 `output/demo_mvp/`에 ARTICLE_DB/INTELLIGENCE_DB(JSONL)와
  대시보드 HTML을 생성한다.
- **자체 발견 버그 수정**: `notifiers.py` 구현 중 `config/notification.yaml`의
  `email`/`telegram` 섹션이 `notifications`의 형제(sibling) 키(중첩이 아님)라는 사실을
  놓쳐, 실제 config로는 수신자 env 변수 이름을 항상 찾지 못하던 문제를 발견해 수정.
  회귀 테스트 `test_load_notification_config_resolves_real_recipient_env_names` 추가.
- 우선순위: TASK-009→010→011→012→013→014→015→017→008 순서(TASK-016 보류)로 전부 진행,
  `TODO.md`/`CLAUDE.md`/`PROJECT_STATUS.md` 갱신.
- 테스트: 신규 8개 파일 68건 추가, 기존 80건과 합쳐 총 **148개 테스트 전부 PASS**.

### Added / Changed — Architect Review Round 3 반영 (2026-08-05, 3차)

ChatGPT Architect Review Round 3(Q1~Q5 + TASK-004C/D/E 추가 지시) 승인 및 반영. Knowledge
Layer를 TASK-009보다 먼저 완성한다는 방향 전환. 외부 API 호출 없음.

- **Q1 (ADR-008)**: Workflow ID는 영구 식별자 — Round 2에서 재배정했던
  `WF-P02/03/04`를 원래 번호 `WF-P08/09/10`로 원복. `docs/decisions/ADR-008-workflow-id-policy.md`
  신규 작성, `config/workflow_registry.yaml`에 결번(WF-P02~P07) 명시.
- **Q2**: Natural Language Admin을 Master Pipeline에 포함하지 않는 기존 판단 승인 (변경 없음).
- **Q3**: `mission`(단일값) → `mission_category`(배열), `mission_subcategory`를 배열로
  변경 — 기사 하나가 복수 축에 걸치는 경우를 처음부터 지원. `schemas/intelligence.schema.json`,
  `schemas/claude_output.schema.json`, `schemas/google_sheets_columns.json`,
  `tests/fixtures/*`, `prompts/*.md`, `knowledge/MISSION_FRAMEWORK.md`,
  `knowledge/ANALYSIS_FRAMEWORK.md` 전부 동기화. 다축 케이스 검증용 fixture
  `intelligence_valid_multi_mission.json` 추가.
- **Q4**: `config/model_registry.yaml` 신설 (classification/deep_analysis/future 3-tier,
  각각 Haiku/Sonnet/Opus 권장). `scripts/claude_client.py:get_model_name()`을
  환경변수→Registry→Prompt embedded fallback 3단계 조회로 재작성. `config/cost_policy.yaml`은
  모델 tier 관리를 model_registry.yaml로 위임.
- **Q5**: 회사 프로필 Knowledge 문서는 16계층 Taxonomy를 예외 없이 전부 포함 — 해당 없는
  계층은 삭제하지 않고 `N/A`로 표기. `knowledge/LX_HOLDINGS_CONTEXT.md` 전면 재작성(6개
  계층 N/A 명시). `knowledge/KNOWLEDGE_POLICY.md` §2.1 "동일 Template 원칙" 추가.
- **TASK-004C (신규) Knowledge Governance**: `knowledge/KNOWLEDGE_GOVERNANCE.md` 작성
  (Version/Review Cycle/Confidence Rule/Source Citation Rule/Conflict Resolution/Evidence
  Priority/Public Information Policy/Last Verified Policy/Archive Policy/Knowledge Quality
  Score 10개 규칙). `scripts/knowledge_quality.py` 신규 — §10 공식을 그대로 구현해 회사
  프로필 문서의 완성도를 정량 측정.
- **TASK-004D (신규) Quick Company Scan Framework**: `knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`
  20개 항목(Company Overview~Reference Sources) 정의, `schemas/quick_company_scan.schema.json`
  신설, `prompts/quick_scan.md`를 20개 항목 출력 구조로 확장. `investment_recommendation`은
  투자 조언이 아닌 절차적 스크리닝 신호(4개 enum)로 설계, `estimated_valuation`은 공개 배수
  없으면 null 강제.
- **TASK-004E (신규) Corporate Intelligence Taxonomy**: `knowledge/INTELLIGENCE_TAXONOMY.md`
  19개 도메인 카테고리(Government~Macro) 정의. `intelligence_categories` 필드를
  `schemas/intelligence.schema.json`(필수), `schemas/claude_output.schema.json`의
  relevance_output(필수)/risk_analysis_output(선택), `schemas/google_sheets_columns.json`의
  INTELLIGENCE_DB에 반영.
- 우선순위 변경: TASK-004C→004D→004E를 TASK-009보다 먼저 완료(이번 라운드에서 전부 완료).
  `TODO.md`/`CLAUDE.md` 갱신.
- 테스트: `tests/test_knowledge_templates.py`(3건), `tests/test_knowledge_quality.py`(6건),
  `tests/test_claude_client.py`에 Model Registry 테스트 6건 추가, `tests/test_schema.py`에
  quick_company_scan/다축 mission/intelligence_categories 테스트 추가. 총 80개 테스트 전부
  PASS.

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
