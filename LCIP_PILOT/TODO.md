# TODO

> 2026-08-05 Architect Review Round 4 반영 후 갱신. TASK-009(Provider Layer)~TASK-017
> (Pilot MVP 통합 테스트)까지 Mock/dry-run 기반 구조와 테스트를 전부 완료했다. 남은 것은
> TASK-016(보류)과 TASK-008(n8n 자동배포, 마지막)뿐이며, 나머지는 사용자가 API
> Key/계정을 준비해야 "실동작"으로 전환할 수 있다.

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

## Claude Code가 다음에 할 작업 — Architect Review Round 4 순서 (전부 완료, Mock 기반)

Round 4는 "Framework Completion"에서 "Working Product Completion"으로 방향을 전환했다.
새 Framework 문서 대신 실제 동작하는 코드/테스트를 완성하는 것이 목표였고, 아래 순서
(TASK-009→010→011→012→013→014→015→017→008, TASK-016 보류)를 이번 라운드에서 전부
Mock/dry-run 기반으로 완료했다. 실제 외부 API 호출은 여전히 시작하지 않았다.

- [x] **TASK-009** Provider Layer — `scripts/providers/`: `AIProvider`(추상) →
      `ClaudeProvider`(모델 조회/Prompt Cache 메시지 구성까지 실동작, 실제 네트워크 호출
      직전에서 `NotImplementedError`로 명시적으로 멈춤, `enabled=False` 기본값) /
      `MockProvider`(결정론적 mock, Pipeline 기본값) / `OpenAIProvider`·`GeminiProvider`
      (미래 확장 stub). 14개 테스트.
- [x] **TASK-010** Source Adapter — `scripts/adapters/`: `SourceAdapter`(추상) →
      `GoogleRSSAdapter`(RSS XML 파싱은 실동작, `http_get` 주입 구조로 실제 네트워크 호출
      없이 테스트, `enabled=False` 기본값) / Naver·DART·정부·IR은 `NotImplementedError`
      stub. 9개 테스트.
- [x] **TASK-011** Analysis Pipeline — `scripts/pipeline/`: Collect→Normalize→Rule
      Filter→Classify→Knowledge Retrieve→Analyze→Validate→Generate Intelligence→Store
      8단계를 분리된 순수 함수로 구현. `ids.py`(ART-/INT- ID 발급), `store.py`(로컬 JSONL —
      실제 Google Sheets 연동 전 dry-run 스탠드인). 14개 테스트.
- [x] **TASK-012** Dashboard Widget — `scripts/dashboard_widgets.py`: Today's
      Change/Risk Tracker/Litigation/Regulation(재사용 가능한 단일 클래스)/**Statistics
      (신규)**/Timeline을 독립 `Widget` 클래스로 분리, `build_dashboard.py`가
      `DEFAULT_WIDGETS` 목록을 조합해 빌드. 기존 함수/토큰과 하위호환 유지. 10개 테스트.
- [x] **TASK-013** Notifier — `scripts/notifiers.py`: `EmailNotifier`/`TelegramNotifier`,
      `config/notification.yaml`의 `test_mode=true`인 동안 dry-run만(`NotifierResult`),
      실제 발송 경로는 명시적으로 차단.
- [x] **TASK-014** Source Health 연동 — `scripts/health_tracking.py`: `SourceAdapter.
      collect()` 실제 호출 결과(성공/응답시간/건수/예외)를 `source_health_check.py`의
      판정 로직에 연결.
- [x] **TASK-015** Cost Guard 연동 — `scripts/cost_tracking.py`: `ProviderUsage`(토큰)를
      `config/model_pricing.yaml` 단가로 환산해 `cost_guard.evaluate()`와 연결 (단가가
      아직 TODO placeholder라 실제 비용은 항상 0으로 계산됨 — 의도된 동작).
      TASK-013/014/015 통합 16개 테스트.
- [x] **TASK-017** Pilot MVP 통합 테스트 + 데모 — `tests/test_mvp_integration.py`가 Round 4
      정의 성공 기준(Google RSS→수집→Rule Filter→Claude 분석→INTELLIGENCE_DB 저장→
      Dashboard 반영→Test Email→Test Telegram)을 그대로 검증(1개, end-to-end). 콘솔
      데모용 `scripts/demo_mvp.py` 추가(`python3 scripts/demo_mvp.py`로 실행 가능).
- [ ] **TASK-016** Natural Language Admin 실연동 — **보류** (Round 4 지시)
- [ ] **TASK-008** n8n API Deployment Tooling (마지막) — 위 항목이 전부 완성된 뒤 실제 n8n
      REST API 자동배포 연동
- [ ] TASK-018 Pilot Deployment

## 이번 라운드(Architect Review Round 4 반영)에서 알려진 한계

- Google Drive/Sheets/n8n/이메일/Telegram/Anthropic API 어떤 것도 실제로 연결·호출되지
  않았다 — Provider/Adapter/Notifier는 전부 `enabled=False`·`test_mode=true` 기본값이며,
  실제 호출 직전에서 `NotImplementedError`/dry-run으로 명시적으로 멈춘다.
- `config/model_registry.yaml`의 모든 `model_id`가 아직 `null`이고, `config/model_pricing.yaml`
  단가도 TODO placeholder(0.0)다 — 실제 모델 확정 전까지 Cost Guard가 계산하는 비용은
  항상 0이다 (임의 추정 금지 원칙에 따른 의도된 동작).
- ARTICLE_DB/INTELLIGENCE_DB는 아직 Google Sheets가 아니라 로컬 JSONL(`scripts/pipeline/
  store.py`)이다 — Google Sheets API 실연동은 TASK-006 dry-run 도구가 승인된 뒤 이
  저장소만 교체하면 되도록 설계했다.
- `GoogleRSSAdapter`는 구조·파싱 로직이 실동작하지만 실제 HTTP 호출은 `enabled=True` +
  사용자 승인 전까지 하지 않는다. Naver/DART/정부/IR Adapter는 API Key/소스 미등록으로
  아직 stub이다.
- Knowledge Base(`knowledge/*.md`)는 Round 3 이후 구조 변경이 없다 — 실제 회사 사실
  리서치(TODO 항목 참고)는 여전히 수행되지 않았다.
- `scripts/demo_mvp.py`/통합 테스트는 TOP-0001 1개 Topic, SRC-0001(Google RSS 영문) 1개
  소스만 다룬다 — 여러 Topic/여러 소스를 동시에 오케스트레이션하는 상위 루프는 아직 없다
  (n8n Master Pipeline이 TASK-008에서 그 역할을 맡을 예정).
