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
   `docs/decisions/ADR-007-n8n-workflow-consolidation.md`
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
    분리된 순수 함수로 구현. 오케스트레이션은 `scripts/demo_mvp.py`가 담당한다.
  - **Dashboard Widget** (`scripts/dashboard_widgets.py`): Today's Change/Risk
    Tracker/Litigation/Regulation(재사용 가능한 단일 클래스)/**Statistics(신규)**/
    Timeline을 독립된 `Widget` 클래스로 분리 — `DEFAULT_WIDGETS` 목록에서 추가/제거해도
    나머지에 영향 없음.
  - Notifier(`scripts/notifiers.py`)/Source Health(`scripts/health_tracking.py`)/
    Cost Guard(`scripts/cost_tracking.py`)도 각각 test_mode dry-run, Adapter 실제 호출
    결과 기반 판정, Provider 사용량 기반 비용 추정으로 연동되었다 — 전부 Mock/dry-run
    기반이며 실제 발송·과금은 발생하지 않는다.
  - `scripts/demo_mvp.py`가 위 전체를 하나의 흐름으로 실행하는 CLI 데모이며,
    `tests/test_mvp_integration.py`가 Pilot MVP 성공 기준(Round 4 정의: Google RSS→
    수집→Rule Filter→Claude 분석→INTELLIGENCE_DB 저장→Dashboard 반영→Test Email→
    Test Telegram)을 그대로 검증한다.
