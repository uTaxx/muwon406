# TODO

> 2026-08-05 Architect Review Round 6 반영 후 갱신. Round 6는 "Engine Development"에서
> "Working Product"로 방향을 전환 — 새 Engine/Framework/Layer 추가를 절대 금지하고,
> Knowledge Base 실제 내용(5개 문서, Quality Score 95.8%)/Company Registry(14개사)/
> Source Registry(11개 Source)를 채우고, News Adapter/Claude Provider를 "구조만"에서
> "실제 코드 존재 + Feature Flag(`config/feature_flags.yaml`)로 안전하게 차단"으로
> 전환했다. 데모는 2개(`demo_mvp.py`+`demo_quick_scan.py`)에서 1개(`demo_pilot.py`)로
> 통합했고, Coverage 대신 품질을 재는 `scripts/quality_gate.py`를 신설했다. 여전히
> Mock/dry-run 기반이며, 남은 것은 TASK-016(보류)과 TASK-008(n8n 자동배포, 마지막) —
> 나머지는 사용자가 API Key/계정을 준비하고 Feature Flag를 켜야 "실동작"으로 전환된다.

## 사용자가 해야 할 작업 (Claude Code가 추정/대신 수행하지 않음)

### 다음 라운드 진행 전 확인 필요 — 03_BUILD_SPECIFICATION.md §24 질문 항목

TASK-009~017의 구조/테스트는 Mock 기반으로 이미 완료됐다 — 아래 항목은 "실제 동작"으로
전환(`ClaudeProvider.enabled=True`, `GoogleRSSAdapter.enabled=True`, `test_mode=False`
등)하기 위해 사용자가 준비해야 하는 것들이며, 아래 중 Claude API 관련 항목이 가장 시급하다.

- [ ] Claude API Key 준비 여부 (Anthropic Console) — **`ClaudeProvider.enabled=True` 전환
      전 필수**
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
- [ ] Gmail OAuth 연결 계정 — `EmailNotifier`를 `test_mode=False` 실제 발송으로 전환할 때 필요
- [ ] Telegram Bot Token / Chat ID 준비 여부 — `TelegramNotifier`를 `test_mode=False` 실제
      발송으로 전환할 때 필요
- [ ] 테스트 수신 이메일 주소(`.env`의 `LCIP_TEST_EMAIL_RECIPIENT`) — 지금도 dry-run
      데모(`scripts/demo_mvp.py`)에서 미설정 시 "(미설정)"으로만 표시됨
- [ ] DART API Key 보유 여부 (Sprint 6 확장 대상)
- [ ] Google Drive Desktop 동기화 사용 여부
- [x] Quick Company Scan 대상 회사 등록 확대 (Round 6 TASK-K02) — `config/
      company_registry.yaml`에 14개사(LX Group 6/국내 경쟁사 2/해외 엔지니어드스톤
      경쟁사 4/일본 경쟁사 2) 등록 완료. LX Hausys(108670) 등 확인된 Ticker는 채웠으나,
      `products`/`value_chain`/`official_website`/`primary_disclosure_source`의 여러
      TODO 항목은 다음 라운드 리서치 대상 — `python scripts/quality_gate.py`의
      Registry Completion으로 진행률 확인 가능(현재 48.8%).

### Knowledge Base — 출처 필요 (우선순위 확정, Architect Review Round 2 Q6)

Round 6 TASK-K01로 우선순위 1~4번, 6번 문서에 WebSearch로 확인한 실제 공개정보를
채웠다 — Knowledge Quality Score 평균 25% → **95.8%** (`python
scripts/knowledge_quality.py --verbose`로 재확인 가능). 남은 것:

1. ~~`LX_HAUSYS_COMPANY_DNA.md`~~ ✅ 91.7% (Section 12 Investment Point는 여전히 draft)
2. ~~`LX_HAUSYS_VALUE_CHAIN.md`~~ ✅ 완료(6개 섹션 + Source/Reference/Confidence footer)
3. ~~`GROUP_RISK_MAP.md`~~ ✅ Section 2 완료
4. ~~`GROUP_OPPORTUNITY_MAP.md`~~ ✅ Section 2 완료
5. [ ] `STRATEGY_PLAYBOOK.md` — Round 6 미착수, 여전히 `confidence: draft`
6. ~~`LX_HOLDINGS_CONTEXT.md`~~ ✅ 100% (Section 10 재무 수치는 단위 확인 필요로 draft 유지)
7. `PLATFORM_CONSTITUTION.md` (이미 완성 — 회사 사실 아님, 낮은 우선순위)

각 항목은 `knowledge/KNOWLEDGE_POLICY.md` §3 서식(Source/Reference URL/Confidence/
Last Verified)을 따라 채운다. 남은 TODO: LX Hausys 미국 법인의 named lawsuit 피고 여부
직접 확인, `LX_HOLDINGS_CONTEXT.md` 재무 수치 단위(억 원/조 원) 원문 대조,
`LX_HAUSYS_COMPANY_DNA.md` Section 12(Investment Point) 작성.

## Claude Code가 다음에 할 작업 — Architect Review Round 4 순서 (전부 완료, Mock 기반)

Round 4는 "Framework Completion"에서 "Working Product Completion"으로 방향을 전환했다.
새 Framework 문서 대신 실제 동작하는 코드/테스트를 완성하는 것이 목표였고, 아래 순서
(TASK-009→010→011→012→013→014→015→017→008, TASK-016 보류)를 이번 라운드에서 전부
Mock/dry-run 기반으로 완료했다. 실제 외부 API 호출은 여전히 시작하지 않았다.

- [x] **TASK-009** Provider Layer — `scripts/providers/`: `AIProvider`(추상) →
      `ClaudeProvider`(모델 조회/Prompt 조립까지 실동작, 실제 네트워크 호출 직전에서
      `NotImplementedError`로 명시적으로 멈춤, `enabled=False` 기본값) /
      `MockProvider`(결정론적 mock, Pipeline 기본값) / `OpenAIProvider`·`GeminiProvider`
      (미래 확장 stub).
- [x] **TASK-010** Source Adapter — `scripts/adapters/`: `SourceAdapter`(추상) →
      `GoogleRSSAdapter`(RSS XML 파싱은 실동작, `http_get` 주입 구조로 실제 네트워크 호출
      없이 테스트, `enabled=False` 기본값) / Naver·DART·정부·IR은 `NotImplementedError`
      stub.
- [x] **TASK-011** Analysis Pipeline — `scripts/pipeline/`: Collect→Normalize→Rule
      Filter→Classify→Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store
      9단계를 분리된 순수 함수로 구현. `ids.py`(ART-/INT- ID 발급), `store.py`(Round 5부터
      `scripts/storage/`의 하위호환 래퍼).
- [x] **TASK-012** Dashboard Widget — `scripts/dashboard_widgets.py`: Today's
      Change/Risk Tracker/Litigation/Regulation(재사용 가능한 단일 클래스)/Statistics/
      Timeline을 독립 `Widget` 클래스로 분리.
- [x] **TASK-013** Notifier — `scripts/notifiers.py`: `EmailNotifier`/`TelegramNotifier`,
      `test_mode=true`인 동안 dry-run만, 실제 발송 경로는 명시적으로 차단.
- [x] **TASK-014** Source Health 연동 — `scripts/source_health_check.py:run_health_check()`
      가 `SourceAdapter.collect()` 실제 호출 결과를 판정 로직에 연결(Round 5에서
      `health_tracking.py`를 이 파일로 병합).
- [x] **TASK-015** Cost Guard 연동 — `scripts/cost_tracking.py`: `ProviderUsage`(토큰)를
      `config/model_pricing.yaml` 단가로 환산해 `cost_guard.evaluate()`와 연결.
- [x] **TASK-017** Pilot MVP 통합 테스트 + 데모 — `tests/test_mvp_integration.py` +
      `scripts/demo_mvp.py`(`python3 scripts/demo_mvp.py`로 실행 가능).
- [ ] **TASK-016** Natural Language Admin 실연동 — **보류** (Round 4 지시, Round 5도 유지)
- [ ] **TASK-008** n8n API Deployment Tooling (마지막) — 위 항목이 전부 완성된 뒤 실제 n8n
      REST API 자동배포 연동
- [ ] TASK-018 Pilot Deployment

## Claude Code가 다음에 할 작업 — Architect Review Round 5 (전부 완료, Mock 기반)

Round 5는 "Pilot을 실제 사용할 수 있는 방향으로 고도화"가 목표였다. Round 4 구조(Provider/
Adapter/Pipeline/Widget)는 그대로 두고, 4개 하위 엔진을 추가하고 Quick Company Scan을
Pilot의 첫 실제 서비스로 승격했다. 여전히 실제 외부 API 호출은 시작하지 않았다.

- [x] **TASK-010A** Storage Backend — `scripts/storage/`: `StorageBackend`(추상) →
      `LocalJSONLStorage`(실동작, Pilot 기본값) / `GoogleSheetsStorage`(구조만,
      `enabled=False`) / `FutureDatabaseStorage`(stub). `pipeline/store.py`는 하위호환
      래퍼로 남기고, `demo_mvp.py`/통합 테스트는 `StorageBackend`를 직접 사용하도록 전환.
- [x] Source Reliability Score — `config/source_reliability.yaml` +
      `scripts/source_priority.py`: 출처 유형별 1~5점, `resolve_conflict()`로 동일 사실
      충돌 시 높은 점수 근거 우선.
- [x] **TASK-009B** Knowledge Retrieval Engine — `scripts/knowledge_engine.py`:
      Section/Topic/Company/Source Priority/Confidence/Last Verified 기준 검색. 부수적으로
      `scripts/knowledge_quality.py`의 4줄 분리 메타데이터 서식 파싱 버그를 함께 고쳤다.
- [x] **TASK-009A** Prompt Engine — `scripts/prompt_engine/`: `PromptTemplate` →
      `PromptBuilder` → `PromptValidator` → `PromptCache`. Static/Knowledge/Source/
      Dynamic/Context 5블록 조립. `ClaudeProvider`가 이 엔진을 사용하도록 전환
      (`prompts/risk_analysis.md` v0.3.0).
- [x] **TASK-012A** Dashboard Data Provider — `scripts/dashboard_data_provider.py`:
      `StaticJSONDataProvider`/`PipelineDashboardDataProvider`(StorageBackend 연동).
      `Widget`을 `get_data()`(구조화 데이터)/`render_html()`(순수 렌더러)로 분리.
- [x] Quick Company Scan 실제 서비스 — `scripts/quick_company_scan.py`,
      `config/company_registry.yaml`: 회사명/Ticker/DART 회사명 → 자동 Source 선택 →
      `AIProvider.quick_company_scan()`(신규 추상 메서드) → Quick Report(스키마 검증) →
      Investment Review 입력.
- [x] Investment Review Engine — `scripts/investment_review.py`,
      `schemas/investment_review.schema.json`: Comparable(Peer 배수) 기반 Valuation만
      계산(DCF는 Enterprise Backlog), Deal Killer 감지, 스크리닝 신호(투자조언 아님).
- [x] Technical Debt 4건 — `claude_client.call_claude_mocked()` 제거, Pricing Key 통일
      (`model_pricing.yaml` 키를 tier 이름과 일치), Dashboard `RegulationWidget` 반복 구성
      정리, `health_tracking.py`를 `source_health_check.py`로 병합.

## Claude Code가 다음에 할 작업 — Architect Review Round 6 (전부 완료, Mock 기반)

Round 6는 "Engine Development"에서 "Working Product"로 방향을 전환했다 — 새 Engine/
Framework/Layer 추가를 절대 금지하고, 실제 데이터를 사용하는 Pilot 완성에 집중했다.

- [x] **TASK-K01** Knowledge Population — `knowledge/LX_HAUSYS_COMPANY_DNA.md` →
      `LX_HAUSYS_VALUE_CHAIN.md` → `LX_HOLDINGS_CONTEXT.md` → `GROUP_RISK_MAP.md` →
      `GROUP_OPPORTUNITY_MAP.md` 순으로 WebSearch 확인 사실만 작성. Quality Score
      25% → 95.8%.
- [x] **TASK-K02** Company Registry — `config/company_registry.yaml` 14개사(Company
      ID/Ticker/Country/Industry/Products/Value Chain/Official Website/Primary
      Disclosure Source).
- [x] **TASK-K03** Source Registry — `config/sources.yaml` 11개 Source(Google RSS/
      Naver/DART/KRX/SEC/EDINET/SEDAR+/Companies House/정부 RSS/기업 IR),
      authentication/rate_limit 필드.
- [x] **TASK-010 변경** 실제 RSS Parser 전환 — `GoogleRSSAdapter.enabled` 기본값이
      `config/feature_flags.yaml`의 `real_network_calls`를 따르도록 전환(여전히
      `false`).
- [x] **TASK-009 변경** 실제 ClaudeProvider — `_call_anthropic()`이 `anthropic` SDK로
      실제 호출하는 코드를 갖되 `feature_flags.claude_api_enabled=False`(현재값)면
      SDK조차 import하지 않고 멈춘다. `scripts/providers/factory.py:get_default_provider()`
      — API Key + Flag 둘 다 있어야 `ClaudeProvider`, 아니면 `MockProvider`.
- [x] **TASK-017 변경** 데모 통합(2→1) — `scripts/demo_pilot.py` 하나로 뉴스수집→Rule
      Filter→Knowledge Retrieval→Claude Analysis→INTELLIGENCE_DB→Dashboard→Quick
      Company Scan→Investment Review→Email/Telegram Preview 전 구간 실행.
- [x] Quality Gate — `scripts/quality_gate.py`: Coverage 대신 품질(Knowledge Quality/
      Registry Completion/Public Source Coverage/Source Freshness/Mock Dependency/
      Pilot Operational Readiness) 측정.
- [x] 중복/데드코드 감사 — `pipeline/store.py`, `claude_client.build_cached_messages()`
      삭제. `build_dashboard.py`의 중복 JSON 로딩을 `StaticJSONDataProvider`로 통합.

## 이번 라운드(Architect Review Round 6 반영)에서 알려진 한계

- Google Drive/Sheets/n8n/이메일/Telegram/Anthropic API 어떤 것도 실제로 연결·호출되지
  않았다 — `config/feature_flags.yaml`의 4개 플래그가 전부 `false`인 한, `ClaudeProvider`/
  `GoogleRSSAdapter`/`GoogleSheetsStorage`/Notifier는 실제 호출 직전에서 명시적으로
  멈춘다(코드는 실제로 존재하지만 도달하지 않는다).
- `config/model_registry.yaml`의 모든 `model_id`가 아직 `null`이고, `config/model_pricing.yaml`
  단가도 TODO placeholder(0.0)다 — 실제 모델 확정 전까지 Cost Guard가 계산하는 비용은
  항상 0이다 (임의 추정 금지 원칙에 따른 의도된 동작).
- ARTICLE_DB/INTELLIGENCE_DB는 아직 Google Sheets가 아니라 `LocalJSONLStorage`(로컬
  JSONL)다 — `GoogleSheetsStorage`는 구조만 있고 `enabled=False`다.
- Naver/DART/정부/IR Adapter는 API Key/소스 미등록으로 아직 stub이다(`scripts/adapters/
  future_adapters.py`, Round 6 감사에서 "Pilot 데모 미호출" 표시 추가).
- `config/company_registry.yaml`은 14개사로 확대됐지만 `products`/`value_chain`/
  `official_website`/`primary_disclosure_source`의 다수 필드가 여전히 TODO다
  (`python scripts/quality_gate.py`의 Registry Completion 48.8%로 정량 확인 가능).
- Investment Review Engine의 Deal Killer 판정은 `risk_assessment` 원문의 키워드 매칭
  수준이다(소송/제재/형사/파산/상장폐지/회계부정) — 고도화는 Enterprise 확장 대상.
- `STRATEGY_PLAYBOOK.md`는 Round 6에서 손대지 않아 여전히 `confidence: draft`다.
- `scripts/demo_pilot.py`/통합 테스트는 TOP-0001 1개 Topic, SRC-0001(Google RSS 영문) 1개
  소스만 다룬다 — 여러 Topic/여러 소스를 동시에 오케스트레이션하는 상위 루프는 아직 없다
  (n8n Master Pipeline이 TASK-008에서 그 역할을 맡을 예정).
