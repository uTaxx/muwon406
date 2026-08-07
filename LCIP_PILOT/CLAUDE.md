# CLAUDE.md — LCIP Pilot 실행 지침

이 파일은 Claude Code가 `LCIP_PILOT/`에서 작업할 때 항상 먼저 읽어야 하는 프로젝트 헌법이다.

## 프로젝트 한 줄 정의

LCIP (LX Corporate Intelligence Platform) Pilot은 **공개정보만** 사용하여 LX홀딩스 전략팀의
**미래준비**(산업·정책·기술·M&A 신호 탐지)와 **리스크 관리**(소송·산업안전·통상·공급망 리스크
조기 감지)를 지원하는 개인용 Corporate Intelligence Pilot이다. 첫 작동 주제는
**엔지니어드스톤·실리코시스 리스크 모니터링** (`TOP-0001`, LX하우시스 관련).

일반 뉴스봇으로 축소 해석하지 말 것 — 모든 기능은 미래준비/리스크관리 미션과 LX 관련성 판단에
연결되어야 한다.

## 절대 원칙 (순서 무관, 전부 항상 적용)

1. 외부 **공개정보만** 사용한다. 내부 보고서·비공개 실적·미공개 거래정보·사내 메신저는 요구하거나
   추정하지 않는다.
2. 모든 핵심 사실에는 원문 URL을 저장한다.
3. 사실·AI 해석·AI 추론·제안을 명확히 구분한다.
4. 모든 분석은 LX홀딩스와 관련 계열사 관점에서 수행한다.
5. AI(Claude API)가 필요 없는 작업(정규화·중복제거·날짜필터·단순계산)에는 AI를 사용하지 않는다.
6. Claude API 월 사용액: 목표 **$15**, 절대 상한 **$20**. 개인 월 총비용(기존 구독 포함)
   **10만원 이하**.
7. Secret(API Key, OAuth Secret, Telegram Token, Chat ID 등)은 `.env` 또는 n8n Credential에만
   저장한다. 코드·Markdown·JSON·Google Sheets·Git에 평문 저장 금지.
8. 실제 외부 쓰기(Google Drive/Sheets 생성, n8n 배포, 이메일·Telegram 발송)는 사용자의 명시적
   승인 전까지 금지한다. 기본은 항상 `dry-run`.
9. n8n 워크플로우는 실행 횟수를 최소화하는 구조를 우선한다. 자동 파이프라인(수집→분석→
   대시보드→알림)은 하나의 Master Pipeline으로 통합하고, 독립 스케줄이 필요한 Source
   Health·Cost Guard와 수동 실행 전용인 Natural Language Admin, 공통 오류 처리인
   Error Handler만 별도 워크플로우로 유지한다 (`docs/decisions/ADR-007-n8n-workflow-consolidation.md`).
10. 변경 사항은 `CHANGELOG.md`와 관련 설계 문서에 반영한다.
11. 문서 간 충돌 시 `docs/decisions/ADR-006-document-priority-policy.md`의 우선순위
    (BUILD_SPECIFICATION → SYSTEM_BLUEPRINT → DEVELOPMENT_MANUAL → HANDOVER)를 따르되,
    Architect Review(사용자 승인을 거친 명시적 지시)가 있으면 그 지시가 최우선이다.

## 작업 절차

1. 프로젝트 루트의 `CLAUDE.md`와 `docs/`의 연결 문서를 모두 읽는다.
2. 수정 전 현재 폴더 구조와 기존 파일을 검사한다.
3. 기존 파일이 있으면 덮어쓰지 말고 diff와 migration 계획을 제시한다.
4. Task 순서는 `docs/03_BUILD_SPECIFICATION.md`의 TASK-001~007을 기본으로 하되, Architect
   Review(2026-08-05, Round 2/3)로 TASK-008 이후 순서가 다음과 같이 조정되었다:
   TASK-004A(Knowledge Foundation Builder) → TASK-004B(Corporate Intelligence Framework)
   → TASK-004C(Knowledge Governance) → TASK-004D(Quick Company Scan Framework) →
   TASK-004E(Corporate Intelligence Taxonomy) — 여기까지 Framework/Knowledge Layer는
   Round 4에서 "Pilot에 충분하다"고 승인되어 **완료 및 동결**되었다. Round 4부터는 새로운
   Framework 문서를 추가하지 않고 ADR만 추가하며, "Framework Completion"에서
   "Working Product Completion"으로 방향을 전환한다. Round 4가 확정한 이후 순서는
   **TASK-009(Provider Layer) → TASK-010(Source Adapter) → TASK-011(Analysis Pipeline) →
   TASK-012(Dashboard Widget) → TASK-013(Notifier)/TASK-014(Source Health)/
   TASK-015(Cost Guard) → TASK-017(Pilot MVP 통합 테스트) → TASK-008(n8n 자동배포, 마지막)**
   이며, TASK-016(Natural Language Admin 실연동)은 보류(on hold)한다. TASK-009~017은
   전부 **Mock/dry-run 기반**으로 구조와 테스트를 완성하는 것이 목표이며, 실제 외부 API
   호출(Anthropic/Google/Gmail/Telegram)은 여전히 시작하지 않는다 (`TODO.md` 참고).
   Architect Review Round 5는 이 위에 4개 하위 확장 Task를 추가했다: **TASK-009A(Prompt
   Engine) / TASK-009B(Knowledge Retrieval Engine) / TASK-010A(Storage Backend) /
   TASK-012A(Dashboard Data Provider)** — Pilot을 "실제 사용할 수 있는" 수준으로
   고도화하는 라운드이며, Quick Company Scan을 Pilot의 첫 번째 실제 서비스로 승격하고
   그 출력을 Investment Review Engine 입력으로 연결한다. Round 5부터도 새 Framework
   문서는 만들지 않고 ADR만 추가하며, 외부 API 실제 연결은 계속 시작하지 않는다.
   Round 6은 "Engine Development에서 Working Product로" 전환해 TASK-K01(Knowledge
   Population)/K02(Company Registry)/K03(Source Registry)로 실제 데이터를 채우고,
   Feature Flag·Provider Factory·Quality Gate를 신설했다. Round 7은 그 위에 Registry
   Engine(RegistryManager)/Knowledge Coverage/Company Registry 30개사 확장/Scenario
   5종/Quality Gate 5개 지표 추가/Connection Readiness 준비를 더했으며, 최종 목표를
   **Pilot Release Candidate(RC1)**로 명시했다 — 이후 라운드는 새 기능보다 Release
   품질에 집중한다. Round 8은 ADR-010으로 RC1 정의를 고정하고, Quick Company Scan을
   Architect 지정 8단계 전체 파이프라인으로 완성하고, Company Intelligence Score를
   신설하고, Dashboard를 Architect 지정 6개 Widget의 Executive Dashboard로 재구성하고,
   Knowledge Coverage에 Company/Country/Industry 3종을 추가하고, RegistryManager에
   Validation/Integrity/Dependency Check를 추가해 Project Boot 시 전체 Registry(8개로
   확장, Technical Debt Registry 신설)를 검증하게 하고, Quality Gate에 Architectural
   Stability/Operational Simplicity/Executive Usability/AI Reasoning Readiness 4개
   지표를 추가했다 — "새로운 Framework는 더 이상 만들지 않는다"는 지시가 이번 라운드부터
   적용된다. Round 9는 Architect가 Platform Architect에서 Product Owner 관점으로
   전환을 선언하며 "사용 가능한 Pilot"을 목표로 삼았다 — 새 구조/Framework/Registry/
   Layer를 추가하지 않고, 우선순위 5개 기능(Quick Company Scan/News Intelligence/
   Investment Review/Executive Dashboard/Email Preview)만 실사용 수준으로 다듬었다.
   가장 큰 성과는 MockProvider가 Round 6이 이미 리서치해 둔 LX Hausys 실제 Knowledge를
   그동안 전혀 쓰지 않고 버리고 있었다는 것을 발견하고 고친 것이다. 상세는 아래
   "Round 6"/"Round 7"/"Round 8"/"Round 9" 절 참고. 외부 API 실제 연결은 Round 9까지도
   시작하지 않았다.
5. 외부 계정에 영향을 주는 작업은 기본적으로 `dry-run`으로 구현한다.
6. 실제 Google Drive·Sheets 생성, n8n 배포, 이메일·Telegram 발송 전 사용자 승인을 요청한다.
7. Task 완료 후 `docs/05_ACCEPTANCE_TESTS.md`의 Acceptance Test를 수행한다.
8. 실패 시 다음 Task로 넘어가지 않는다.
9. 각 Task 완료 시 `PROJECT_STATUS.md`, `TODO.md`, `CHANGELOG.md`를 갱신한다.
10. 완료 주장은 생성 파일·테스트 결과·남은 사용자 작업을 제시한 뒤에만 한다.

## 먼저 읽을 문서 (읽는 순서)

문서 우선순위 정책은 `docs/decisions/ADR-006-document-priority-policy.md` 참고
(BUILD_SPECIFICATION → SYSTEM_BLUEPRINT → DEVELOPMENT_MANUAL → HANDOVER).

1. `docs/03_BUILD_SPECIFICATION.md` — 실행 명세서 (Task 정의의 최종 근거)
2. `docs/02_SYSTEM_BLUEPRINT.md`
3. `docs/DEVELOPMENT_MANUAL_REFERENCE.md`
4. `docs/01_PROJECT_CONTEXT.md`
5. `docs/04_DATA_AND_CONFIG_SCHEMA.md`, `docs/decisions/ADR-006-document-priority-policy.md`,
   `docs/decisions/ADR-007-n8n-workflow-consolidation.md`, `docs/CONNECTION_READINESS.md`
   (Round 7 — 실제 API 연결 전 준비사항, 실제 호출은 하지 않음)
6. `knowledge/KNOWLEDGE_POLICY.md`, `knowledge/MISSION_FRAMEWORK.md`,
   `knowledge/SOURCE_PRIORITY.md`, `knowledge/ANALYSIS_FRAMEWORK.md`,
   `knowledge/INVESTMENT_FRAMEWORK.md` — Corporate Intelligence Framework (TASK-004B)
7. `knowledge/KNOWLEDGE_GOVERNANCE.md`(TASK-004C), `knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`
   (TASK-004D), `knowledge/INTELLIGENCE_TAXONOMY.md`(TASK-004E) — Knowledge Engine 3종
8. Knowledge 파일 우선순위(Architect Review Round 2 Q6, `knowledge/KNOWLEDGE_POLICY.md` §4):
   `LX_HAUSYS_COMPANY_DNA.md` → `LX_HAUSYS_VALUE_CHAIN.md` → `GROUP_RISK_MAP.md` →
   `GROUP_OPPORTUNITY_MAP.md` → `STRATEGY_PLAYBOOK.md` → `LX_HOLDINGS_CONTEXT.md` →
   `PLATFORM_CONSTITUTION.md`
9. `schemas/*.json`
10. `config/*.yaml`

파일이 없으면 Blueprint 기준으로 템플릿을 생성하되, 임의의 기업 사실은 작성하지 않고 TODO와
필요한 출처를 표시한다 (`knowledge/KNOWLEDGE_POLICY.md` §2~3의 16계층 Taxonomy와 서식을
따른다).

## 하지 말아야 할 것

- 과도한 프레임워크·추상화 도입
- 별도 DB(PostgreSQL 등)를 Pilot 단계에서 먼저 구축
- 모든 소스를 한 번에 연결
- 기사 원문 전체를 그대로 Claude에 전달 (요약·발췌만)
- Prompt를 n8n 노드 안에만 숨겨두기 (반드시 `prompts/*.md`로 버전관리)
- API Key 하드코딩
- 회사 내부정보를 요구하거나 추정
- 근거 없는 LX 영향 단정
- Pilot 단계에서 Enterprise 기능(다중사용자, 관리자포털, 전 계열사 자동화)까지 무리하게 구현

## 참고: 설계문서 간 알려진 충돌/불일치 및 Architect Review 반영사항

`docs/04_DATA_AND_CONFIG_SCHEMA.md`의 "설계문서 충돌 로그" 절과 ADR-006/ADR-007을 참고. 요약:

- 문서 우선순위: `docs/decisions/ADR-006-document-priority-policy.md`
  (BUILD_SPECIFICATION → SYSTEM_BLUEPRINT → DEVELOPMENT_MANUAL → HANDOVER).
- Google Drive 폴더 구조는 `03_BUILD_SPECIFICATION.md` TASK-005 기준(`config/drive_structure.yaml`)을
  따르고, Blueprint의 8-폴더 구조는 참고용으로만 남긴다.
- Google Sheets 탭은 11개(`CHANGE_LOG` 포함) 전부 생성하며, 전 탭이 `confirmed` 상태다
  (Architect Review Q2로 컬럼 확정, `config/sheet_structure.yaml`).
- n8n 워크플로우는 `docs/decisions/ADR-007-n8n-workflow-consolidation.md`에 따라 Master
  Pipeline 구조로 통합되어 있다 (5개 파일: Master Pipeline, Source Health, Cost Guard,
  Natural Language Admin, Error Handler).
- Claude 모델은 1차 분류에 Haiku 계열, 심층분석에 Sonnet 계열, 미래준비 고품질 분석(Quick
  Company Scan 등)에 Opus 계열을 권장한다. 실제 모델 ID는 `config/model_registry.yaml`이
  단일 진실 공급원이며, 조회 순서는 환경변수(.env) → Registry → Prompt embedded fallback
  이다(`scripts/claude_client.py:get_model_name()`, Architect Review Round 3 Q4). 코드
  하드코딩 금지 원칙은 불변. Prompt는 Static Block(Knowledge/LX Context/Strategy
  Context/Header, 캐시 대상)과 Dynamic Block(요청별 내용)으로 분리한다.
- **Workflow ID는 영구 식별자이며 재배정하지 않는다** (`docs/decisions/ADR-008-workflow-id-policy.md`,
  Architect Review Round 3 Q1). Source Health/Cost Guard/Natural Language Admin은 원래
  번호(WF-P08/P09/P10)를 유지한다. WF-P02~WF-P07은 Master Pipeline에 흡수된 결번으로 영구
  보존하며 다른 역할에 재사용하지 않는다.
- `mission_category`/`mission_subcategory`/`intelligence_categories`는 Pilot 초기부터
  **배열(Array)**로 설계한다 (Architect Review Round 3 Q3, TASK-004E) — 기사 하나가 여러
  축·카테고리에 동시에 해당하는 경우가 흔하기 때문이다. `intelligence_categories`는
  `knowledge/INTELLIGENCE_TAXONOMY.md`의 19개 도메인 카테고리를 따르며 목적 축
  (`mission_category`)과는 독립적으로 함께 사용된다.
- 회사 프로필류 Knowledge 문서(`LX_HAUSYS_COMPANY_DNA.md`, `LX_HOLDINGS_CONTEXT.md`, 향후
  Quick Company Scan 산출물)는 16계층 Taxonomy를 예외 없이 동일하게 포함하며, 해당 없는
  계층은 삭제하지 않고 `N/A`로 표기한다 (Architect Review Round 3 Q5,
  `knowledge/KNOWLEDGE_POLICY.md` §2.1).
- Knowledge Engine 3종(TASK-004C/D/E)이 추가되었다: `KNOWLEDGE_GOVERNANCE.md`(버전·검토주기·
  신뢰도·인용·충돌해결·아카이브·품질점수 규칙, `scripts/knowledge_quality.py`로 측정),
  `QUICK_COMPANY_SCAN_FRAMEWORK.md`(20항목, `schemas/quick_company_scan.schema.json`),
  `INTELLIGENCE_TAXONOMY.md`(19개 도메인 카테고리).
- **Workflow ID는 Active/Deprecated/Archived 3단계 생명주기로 관리한다**
  (`docs/decisions/ADR-009-workflow-lifecycle-policy.md`, Architect Review Round 4 Q1,
  `config/workflow_registry.yaml`의 `lifecycle_stage` 필드).
- `intelligence_categories`는 `relevance_output`뿐 아니라 `risk_analysis_output`에서도
  **필수**다 (Architect Review Round 4 Q2) — `mission_category`(목적 축)와
  `intelligence_categories`(도메인 축)는 항상 함께, 서로 독립적으로 채운다.
- Quick Company Scan은 **Core(필수 7개)/Advanced(선택 13개)**로 분리되었다
  (Architect Review Round 4 Q3, `schemas/quick_company_scan.schema.json`,
  `knowledge/QUICK_COMPANY_SCAN_FRAMEWORK.md`). Pilot은 Core만으로 보고서를 생성할 수
  있어야 하며, Enterprise 단계에서 Advanced까지 채운다.
- **Round 4부터 "Working Product Completion" 단계다** — 새 Framework 문서 대신 실제
  동작하는 코드/테스트를 늘린다. 핵심 아키텍처 패턴 4가지:
  - **Provider Layer** (`scripts/providers/`): `AIProvider`(추상) → `ClaudeProvider`
    (구조는 실동작, `enabled=False` 기본값으로 실제 호출은 여전히 차단)/`MockProvider`
    (결정론적 mock, Pipeline 기본값)/`OpenAIProvider`·`GeminiProvider`(미래 확장 stub).
  - **Source Adapter** (`scripts/adapters/`): `SourceAdapter`(추상) →
    `GoogleRSSAdapter`(RSS 파싱은 실동작, `enabled=False` 기본값으로 실제 HTTP는 차단,
    `http_get` 주입으로 테스트)/Naver·DART·정부·IR은 `NotImplementedError` stub.
  - **Analysis Pipeline** (`scripts/pipeline/`): Collect→Normalize→Rule Filter→
    Classify→Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store를
    분리된 순수 함수로 구현. 오케스트레이션은 당시 `scripts/demo_mvp.py`가 담당했다
    (Round 6에서 `demo_pilot.py`로 통합, Round 7부터 `scripts/scenarios/*.py` 5종
    Scenario로 대체 — 아래 Round 7 절 참고).
  - **Dashboard Widget** (`scripts/dashboard_widgets.py`): Today's Change/Risk
    Tracker/Litigation/Regulation(재사용 가능한 단일 클래스)/**Statistics(신규)**/
    Timeline을 독립된 `Widget` 클래스로 분리 — `DEFAULT_WIDGETS` 목록에서 추가/제거해도
    나머지에 영향 없음.
  - Notifier(`scripts/notifiers.py`)/Source Health(`scripts/source_health_check.py`의
    `run_health_check()`)/Cost Guard(`scripts/cost_tracking.py`)도 각각 test_mode
    dry-run, Adapter 실제 호출 결과 기반 판정, Provider 사용량 기반 비용 추정으로
    연동되었다 — 전부 Mock/dry-run 기반이며 실제 발송·과금은 발생하지 않는다.
  - 당시 `scripts/demo_mvp.py`가 위 전체를 하나의 흐름으로 실행하는 CLI 데모였으며,
    `tests/test_mvp_integration.py`가 Pilot MVP 성공 기준(Round 4 정의: Google RSS→
    수집→Rule Filter→Claude 분석→INTELLIGENCE_DB 저장→Dashboard 반영→Test Email→
    Test Telegram)을 그대로 검증한다(이 통합 테스트 자체는 지금도 유효 — 파일 삭제
    이력과 무관하게 동일 흐름을 자체 재구현해 검증한다).
- **Round 5: "Pilot을 실제 사용할 수 있는 방향으로 고도화"** — Round 4 구조를 유지한 채
  4개 하위 엔진을 추가하고, Quick Company Scan을 Pilot 첫 실제 서비스로 승격했다.
  - **Storage Backend** (`scripts/storage/`): `StorageBackend`(추상) →
    `LocalJSONLStorage`(실동작, Pilot 기본값)/`GoogleSheetsStorage`(구조만, `enabled=False`
    기본값)/`FutureDatabaseStorage`(stub). Pipeline은 이 인터페이스만 참조한다.
    (Round 6 데드코드 정리: 당시 하위호환용으로 남겨뒀던 `scripts/pipeline/store.py`
    래퍼는 실제 호출자가 자기 자신의 테스트뿐이었음이 확인되어 삭제했다 — 저장 로직은
    `scripts/storage/`에만 존재한다.)
  - **Source Reliability Score** (`config/source_reliability.yaml`,
    `scripts/source_priority.py`): 출처 유형별 1~5점(정부/기업IR/DART/SEC=5, 로이터=4,
    Google RSS=3, 블로그=2, SNS=1). `resolve_conflict()`로 동일 사실 충돌 시 높은 점수
    근거를 우선한다. 기존 `reliability_grade`(A/B/C, Source 단위)와는 별도 축이다.
  - **Knowledge Retrieval Engine** (`scripts/knowledge_engine.py`): knowledge/*.md를
    Section 단위로 파싱해 Section/Topic/Company/Source Priority/Confidence/Last
    Verified 기준으로 검색 가능하게 한다. 이 과정에서 `scripts/knowledge_quality.py`가
    4줄 분리 메타데이터 서식(`LX_HAUSYS_COMPANY_DNA.md` 등)을 인식하지 못해 항상
    Quality Score 0%로 오판정하던 버그를 함께 고쳤다.
  - **Prompt Engine** (`scripts/prompt_engine/`): `PromptTemplate` → `PromptBuilder` →
    `PromptValidator` → `PromptCache` → Provider. Static/Knowledge/Source/Dynamic/
    Context 5개 Block으로 조립하며, Static/Knowledge/Source Block은 캐시 대상이다.
    `ClaudeProvider`가 `claude_client.build_cached_messages()` 대신 이 엔진을 사용하며,
    `lx_context_excerpt`는 Knowledge Block, 기사 출처의 Source Reliability Score는
    Source Block으로 들어간다(`prompts/risk_analysis.md` v0.3.0).
  - **Dashboard Data Provider** (`scripts/dashboard_data_provider.py`): Data
    Provider(`StaticJSONDataProvider`/`PipelineDashboardDataProvider`) → Widget →
    Dashboard 구조. `Widget`은 이제 `get_data(data)`(구조화 데이터, HTML 아님)와
    `render_html(widget_data)`(순수 렌더러)로 나뉜다 — `render()`는 하위호환용으로
    `render_html(get_data(data))`를 호출하는 조합으로만 남아 있다.
  - **Quick Company Scan 실제 서비스** (`scripts/quick_company_scan.py`,
    `config/company_registry.yaml`): 회사명/Ticker/DART 회사명 입력 →
    `resolve_company_input()`(레지스트리에 없으면 임의로 지어내지 않고 `resolved=False`) →
    `select_sources_for_company()`(국가/DART 등록 여부로 자동 선택) →
    `AIProvider.quick_company_scan()`(신규 추상 메서드, Core 7개 스키마 준수) →
    `build_quick_report()`(스키마 검증) → `build_investment_review_input()`.
  - **Investment Review Engine** (`scripts/investment_review.py`,
    `schemas/investment_review.schema.json`): Comparable(Peer EV/EBITDA·PER·PBR) 기반
    Valuation만 계산한다 — **DCF는 Enterprise Backlog**(Pilot 범위 아님). Deal Killer
    키워드가 발견되면 다른 조건과 무관하게 `recommendation.signal =
    decline_deal_killer_found`로 덮어쓴다. 최종 투자판단이 아니라 스크리닝 신호까지만
    제공한다(`knowledge/INVESTMENT_FRAMEWORK.md`와 동일 원칙).
  - **Technical Debt 정리**: `claude_client.call_claude_mocked()`(및 `ClaudeUsage`/
    `ClaudeCallResult`) 제거 — `providers.mock_provider.MockProvider`로 완전히
    대체됨. `config/model_pricing.yaml`의 키를 `model_registry.yaml`의 tier 키
    (classification/deep_analysis/future)와 통일해 `cost_tracking.py`의 이중 매핑
    테이블(TIER_TO_PRICING_KEY)을 제거. `dashboard_widgets.py`의 `RegulationWidget` 3회
    반복 생성을 설정 목록 기반으로 정리. `scripts/health_tracking.py`를
    `scripts/source_health_check.py`로 병합(파일명은 `03_BUILD_SPECIFICATION.md` 원문
    기준 유지).
- **Round 6: "Engine Development에서 Working Product로 전환"** — 새 Engine/Framework/
  Layer 추가를 절대 금지하고, 실제 데이터를 채우는 데 집중했다. 아키텍처는 Round 4/5에서
  동결.
  - **TASK-K01/K02/K03**: `knowledge/*.md` 5개 문서에 WebSearch로 확인한 실제 공개정보
    작성(Knowledge Quality Score 25%→95.8%), `config/company_registry.yaml` 1→14개사,
    `config/sources.yaml` 4→11개 Source(authentication/rate_limit 필드 신설).
  - **Feature Flag** (`config/feature_flags.yaml`, `scripts/feature_flags.py`): 개별
    `enabled=` 인자보다 상위의 전역 안전장치. 4개 스위치(`real_network_calls`/
    `claude_api_enabled`/`google_sheets_enabled`/`notification_send_enabled`) 전부
    다음 Architect 승인 전까지 `false`.
  - **TASK-009/010 실체화**: `ClaudeProvider._call_anthropic()`이 실제 `anthropic` SDK
    호출 코드를 갖되 `feature_flags.claude_api_enabled`가 `false`인 한 SDK import조차
    하지 않고 멈춘다(2중 게이트). `scripts/providers/factory.py:get_default_provider()`
    신설 — API Key + Flag 둘 다 있어야 `ClaudeProvider`, 아니면 `MockProvider`.
    `GoogleRSSAdapter.enabled` 기본값도 `real_network_calls` 플래그를 따르도록 전환.
  - **데모 통합(2→1)**: `demo_mvp.py`+`demo_quick_scan.py`를 `scripts/demo_pilot.py`
    하나로 통합(Round 7에서 다시 Scenario 5종으로 대체 — 아래 참고).
  - **Quality Gate** (`scripts/quality_gate.py`): Coverage 대신 품질을 측정한다.
    Knowledge Quality/Registry Completion/Public Source Coverage/Source Freshness/
    Mock Dependency/Pilot Operational Readiness 6개 지표(Round 7이 5개 추가 — 아래 참고).
  - **데드코드/중복 구조 정리**: `scripts/pipeline/store.py`(실제 호출자가 자기
    테스트뿐이었음), `claude_client.build_cached_messages()`(Prompt Engine으로 완전
    대체되어 미사용) 삭제. `build_dashboard.py`의 중복 JSON 로딩을
    `dashboard_data_provider.StaticJSONDataProvider` 재사용으로 교체.
    `future_providers.py`/`future_adapters.py`/`future_storage.py`(Round 4/5가 승인한
    확장 지점 stub)에는 "Pilot이 호출하지 않는다"는 감사 표시만 추가하고 삭제하지
    않았다 — Provider/Adapter/Storage 교체 가능성의 증거이기 때문이다.
- **Round 7: "Registry 통합 + Coverage 전환 + Scenario화 + Connection Readiness 준비"**
  — 최종 목표는 **Pilot Release Candidate(RC1)**이며, 이후 라운드는 새 기능보다 Release
  품질에 집중한다.
  - **RegistryManager** (`scripts/registries/`): Company/Source/Model/Prompt/Workflow/
    Config/Storage 7개 Registry에 동일 Interface(`list_entries`/`get`/`count`)를
    씌우는 얇은 어댑터 계층 — 새 Engine이 아니라 각 Registry의 원본 파일(YAML/파일
    목록)은 그대로 두고 조회 방식만 통일한다. 기존 호출부(`quick_company_scan.py`가
    `config/company_registry.yaml`을 직접 읽는 것 등)는 그대로 유지된다.
  - **Knowledge Coverage** (`scripts/knowledge_coverage.py`): Knowledge Quality를
    "문서 개수"가 아니라 "도메인 커버리지"로 전환 — Corporate/Market/Competitor/
    Government/Technology/Risk/Opportunity/Investment 8개 도메인을 (파일, Section
    번호) 명시적 매핑으로 채점한다(키워드 유사 매칭이 아니다 — 같은 단어가 다른
    도메인을 가리키는 경우가 있어서다). `knowledge_quality.py`의 12계층 채점 로직을
    그대로 재사용한다.
  - **Company Registry 14→30개사**: LG전자/LG화학(별도 그룹사 — LX와 혼동 주의)/
    글로벌 유리 제조사(Saint-Gobain/AGC/NSG/Guardian/Vitro)/글로벌 창호 제조사(Schüco/
    Rehau/Deceuninck/Andersen/Pella/Marvin)/PPG + Claude가 30개사 목표 달성을 위해
    추가 선정한 Corning/Owens Corning.
  - **Source Registry**: 11개 Source 전부에 `estimated_update_delay`/
    `typical_reliability`/`historical_stability` 필드 추가(전부 "Pilot 자체 연동
    이력 없음"으로 정직하게 표시 — feature flag가 꺼져 있는 한 사실이다).
  - **Scenario 5종** (`scripts/scenarios/`): "하나의 통합 데모" 대신 독립 실행 가능한
    5개 Scenario로 전환 — 뉴스 분석(1)/Quick Company Scan(2)/Investment Review(3,
    내부적으로 2를 호출)/정부 정책 영향 분석(4, `AIProvider.analyze_policy_impact()`
    신규 메서드 + `policy_analysis_output` 스키마 신설, 기존 `prompts/policy_analysis.md`를
    처음으로 실제 연결)/경쟁사 변화 감지(5, 스냅샷 diff — 최초 실행은 "최초 스냅샷"으로
    정직하게 보고). `scripts/demo_pilot.py`는 삭제됐다.
  - **Quality Gate 5개 지표 추가**(전부 100점 만점): Registry Quality(RegistryManager
    구조+내용), Report Quality(Scenario 2/3를 실제로 실행해 스키마 검증 실측),
    Evidence Quality(Knowledge Coverage+Registry Completion 평균), Reasoning
    Quality(**설계 proxy임을 반드시 유지 — 실제 출력 품질 아님**, risk_analysis/
    policy_analysis 프롬프트가 confidence/evidence/unknowns를 요구하는지만 확인),
    Maintainability(`scripts/` 모듈 docstring 비율).
  - **Connection Readiness** (`docs/CONNECTION_READINESS.md`): 실제 API 연결 없이
    Credential 체크리스트/환경변수(`.env.example`에 Naver/모델 3종/테스트 수신 이메일
    보강)/Connection Test Plan/Rollback Plan만 준비한다. 실제 호출은 다음 Architect
    승인 이후 시작한다 — Round 7도 예외 없이 외부 API를 한 건도 호출하지 않았다.
  - Investment Review Engine은 Round 5와 동일하게 Comparable 기반만 유지한다(DCF/
    LBO/Option은 계속 Enterprise Backlog).
- **Round 8: "Architecture 중심에서 Product 중심으로 전환 완료 — Pilot RC1을 향한 마지막
  다듬기"** — "새로운 Framework는 더 이상 만들지 않는다"와 "전략팀 시연 관점에서만
  개발한다. 새 기능보다 사용성/품질/완성도를 우선한다"가 이번 라운드부터 적용되는 절대
  제약이다.
  - **ADR-010 Release Policy**: RC1 = "실제 API 없이도 전략팀 데모가 가능한 수준"
    (Mock+Feature Flag+실제 Pipeline+실제 Registry+실제 Dashboard)로 정의를 고정했다.
    RC2(실제 API 연결)로 넘어가는 경계와, `FinancialDataProvider`가 새 Framework가
    아니라 기존 Provider Layer 패턴의 재적용임을 명시한다.
  - **Quick Company Scan 8단계 완성**: Input→Company Registry→Knowledge Retrieval→
    Source Selection→**Financial Provider(Mock)**→Analysis Pipeline→Investment
    Review→Dashboard Widget→Export. Financial Provider(`scripts/financial_provider.py`)
    만 Mock이고 나머지는 전부 실제 코드다. `retrieve_knowledge_for_company()`가
    `knowledge_engine.search_by_company()`를 통해 Knowledge Base 발췌를
    `AIProvider.quick_company_scan()`(신규 `knowledge_excerpt` 파라미터, 하위호환)에
    전달한다. `export_quick_scan_report()`가 JSON/Markdown 산출물을 생성한다.
  - **Company Intelligence Score** (`scripts/company_intelligence_score.py`): Business
    Understanding/Market Position/Financial Visibility/Strategic Importance/Risk
    Visibility/Source Reliability/Knowledge Coverage 7개 하위 점수(완성도 기반, 각
    100점 만점)와 평균인 `overall`. Scenario 3이 실행할 때마다 계산해 저장한다.
  - **Executive Dashboard 6개 Widget**: 기존 소송·규제 특화 Widget 6종을 전부 제거하고,
    Architect 지정 우선순위(Today's Intelligence→Critical Risk→Future Opportunity→
    Quick Company Scan→Investment Review→Source Health) 그대로 재구성했다(`scripts/
    dashboard_widgets.py`). Scenario 1/3이 `output/pilot_data/`를 공유해 하나의
    Executive Dashboard가 두 Scenario 산출물을 함께 반영한다("각 Scenario가 실행 시점
    데이터로 독립적으로 dashboard.html을 다시 쓴다"는 특성은 알려진 한계로 Technical
    Debt Registry에 등록됨 — TD-006).
  - **Knowledge Coverage 3종 추가** (`scripts/knowledge_coverage.py`): 기존 8개 도메인
    Coverage에 Company/Country/Industry Coverage를 추가했다. Company Coverage는
    Company Registry 30개사 중 신뢰 가능한 Knowledge를 실제로 가진 비율(3.3% —
    LX_HAUSYS 1개사뿐), Country Coverage는 등장 국가 중 `active: true` Source가 있는
    비율(22.2%, `country: multi` placeholder는 실질 커버리지로 세지 않음), Industry
    Coverage는 정확 문자열 매칭만 쓴다(3.6%). 전부 부풀리지 않은 실측치다. Quality
    Gate의 Evidence Quality 계산식(8개 도메인 평균)은 조용히 바꾸지 않았다.
  - **RegistryManager Validation/Integrity/Dependency Check**: "Registry는 조회만
    하지 않는다" 지시에 따라 `scripts/registries/validation.py`를 신설하고
    `RegistryManager`에 `validate()`/`check_integrity()`/`check_dependencies()`/
    `validate_all()`을 추가했다. `bootstrap_project.py`(Project Boot)가
    `validate_all()`을 호출해 매 부트마다 전체 Registry를 검증한다.
  - **Technical Debt Registry** (`config/technical_debt_registry.yaml`): 코드 감사로
    실제 확인한 부채 항목을 Severity/Priority/Estimated Time/Owner/Status 필드로
    관리한다("실제 프로젝트 관리가 가능해야 한다"). 새 Registry 어댑터를 만들지 않고
    기존 `YAMLListRegistry`를 재사용해 RegistryManager의 8번째 Registry로 등록했다.
  - **Quality Gate 4종 지표 추가**(전부 100점 만점): Architectural Stability(`scripts/`
    패키지 집합이 Round 7/8 기준선과 정확히 같은지 비교 — "새 Framework 금지"를 직접
    계측), Operational Simplicity(5개 Scenario가 단일 명령으로 끝까지 실행되는지 실제
    서브프로세스로 실측), Executive Usability(`sample_data.json` 기준 `build_html()`
    호출로 6개 Widget 섹션 렌더링 실측), AI Reasoning Readiness(`ClaudeProvider`가
    `AIProvider`의 4개 추상 메서드 전부를 실제 Prompt Engine 경로까지 연결했는지 소스
    코드로 확인 — Reasoning Quality와 다른 축).
  - 외부 API 실제 연결은 Round 8도 예외 없이 시작하지 않았다.
- **Round 9: "사용 가능한 Pilot"** — Architect가 Platform Architect에서 Product Owner
  관점으로 전환을 선언했다. "이번 Round부터는 새로운 구조, Framework, Registry, Layer를
  추가하지 않는다." 목표 우선순위 고정: 1) Quick Company Scan, 2) News Intelligence,
  3) Investment Review, 4) Executive Dashboard, 5) Email Preview — 이 외 기능은 이번
  Sprint에서 구현하지 않는다. 새 기능보다 삭제/단순화/사용성/완성도를 우선한다.
  - **MockProvider가 실제 Knowledge Base를 실제로 쓰도록 수정**: Round 6이 LX Hausys에
    대해 실제로 리서치해 채워둔 Knowledge(`LX_HAUSYS_COMPANY_DNA.md`)를, Round 8까지의
    MockProvider는 전혀 쓰지 않고 항상 "mock: ... 미확인"만 반환하고 있었다 — Round 9가
    발견하고 고친 가장 큰 성과다. `company_id`가 있으면 그 회사의 1순위 Knowledge
    문서(§1 Company/§2 Business/§3 Product/§7 Competitor, `knowledge_quality.py`와
    동일한 신뢰 가능 판정)를 그대로 노출한다 — Claude는 여전히 호출하지 않는다
    (confidence는 계속 "low"). 처음에는 `search_by_company()`가 이어붙이는 7개 파일
    전체에서 Section 번호로만 찾다가, LX_HOLDINGS_CONTEXT.md도 §7을 가진다는 사실 때문에
    지주회사의 문장이 잘못 노출되는 버그가 있었다 — knowledge_coverage.py가 이미 "(파일,
    Section 번호) 명시적 쌍"을 쓰는 이유와 동일한 이유로, 1순위 문서 하나만 직접 파싱하는
    방식으로 수정했다.
  - **Quick Company Scan Export 전면 재작성**: 이전에는 Company Overview 한 줄만
    보여주고 Business Structure/Product Portfolio/Financial Snapshot/Competitor/LX
    Strategic Fit/Unknowns/Reference Sources/Comparable Peer 표를 전부 누락했다 —
    "실제 전략팀 직원이 바로 사용할 수 있는가?"에 정직하게 답하기 위해 Core 7 필드
    전부와 Investment Review 세부(추천 사유/Peer 비교표)를 한 페이지에 담도록 재작성했다.
  - **News Intelligence에 Email Preview 단계 추가**: "뉴스 1건→Rule Filter→AI 분석→
    Dashboard→Email Preview→완료"를 하나의 Pipeline으로 만들라는 지시에 따라, Scenario
    1의 마지막 단계로 Round 4의 `notifiers.EmailNotifier`+`build_alert_message()`를
    그대로 재사용해 Email Preview(dry-run, 실제 발송 없음)를 추가했다(6단계→7단계).
  - **Investment Review Backlog 재확인**: DCF(Round 5)에 이어 LBO/Option/PMI(Post-Merger
    Integration)도 Enterprise Backlog로 명시 재확인했다(`knowledge/INVESTMENT_FRAMEWORK.md`
    §4, `scripts/investment_review.py` 모듈 docstring) — 넷 다 지금까지 구현된 적이
    없으므로 코드 변경은 없다.
  - **Executive Dashboard 가독성 개선(새 Widget 없음)**: `scripts/pipeline/
    dashboard_feed.py`의 행(row) 딕셔너리 키를 원본 필드명(created_at/fact_summary 등)
    대신 한글 라벨(날짜/핵심 내용/신뢰도/출처 등)로 바꿨다 — `render_generic_list()`가
    dict key를 그대로 테이블 헤더로 쓰기 때문에 이 접착 함수만 바꿔도 6개 Widget 전부의
    가독성이 개선된다. 또한 Scenario를 반복 실행할수록 같은 내용이 계속 쌓여 중복
    표시되는 문제를 실사용 중 발견해, `_most_recent()`로 최신 10건만 노출하도록
    수정했다(Storage 자체는 감사 목적으로 전체를 그대로 보존한다).
  - **Company Registry/Knowledge/Coverage는 Pilot에 필요한 수준까지만**: Round 9는
    "TODO를 모두 채우려고 하지 않는다"고 명시했다 — 이번 라운드는 신규 리서치를 수행하지
    않고, `config/technical_debt_registry.yaml`(TD-005/007)에 이미 등록된 리서치 과제를
    "전체 30개사"가 아니라 "TOP-0001 핵심 비교군부터"로 범위를 좁히는 방향을 다음
    라운드 승인 사항으로 남겼다(Pilot 검증 중 Caesarstone처럼 핵심 비교군인데도
    Knowledge가 전혀 없는 회사를 직접 확인함).
  - 외부 API 실제 연결은 Round 9도 예외 없이 시작하지 않았다. 새로운 구조/Framework/
    Registry/Layer도 추가하지 않았다(지시 그대로 — 기존 코드 수정만 수행).
