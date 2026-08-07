# Changelog

모든 주요 변경사항을 이 파일에 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/)를
느슨하게 따른다.

## [Unreleased]

### Added — Architect Review Round 8 반영 (2026-08-07, 8차)

ChatGPT Architect Review Round 8 승인 및 반영. "현재 LCIP는 Architecture 중심
프로젝트에서 Product 중심 프로젝트로 성공적으로 전환되었다"고 평가하고, 이번 라운드부터
**Pilot RC1(Release Candidate)**를 목표로 개발하도록 지시했다. "새로운 Framework는 더
이상 만들지 않는다", "전략팀 시연 관점에서만 개발한다. 새 기능보다 사용성/품질/완성도를
우선한다. 실제 API 호출은 계속 금지한다"가 이번 라운드의 핵심 제약이다.

- **ADR-010 Release Policy**: RC1을 "실제 API를 사용하지 않아도 전략팀 데모가 가능한
  수준" = Mock 기반 + Feature Flag + 실제 Pipeline + 실제 Registry + 실제 Dashboard로
  정의 고정. RC2(실제 API 연결)로의 경계와, `FinancialDataProvider`가 새 Framework가
  아니라 기존 Provider Layer 패턴의 재적용임을 명시했다.
- **Quick Company Scan 8단계 파이프라인 완성**: Architect가 지정한 순서(Input→Company
  Registry→Knowledge Retrieval→Source Selection→Financial Provider(Mock)→Analysis
  Pipeline→Investment Review→Dashboard Widget→Export)를 전부 실제 코드로 연결했다.
  "Pilot에서는 Financial Provider만 Mock, 나머지는 실제 코드" 지시대로
  `scripts/financial_provider.py`(`FinancialDataProvider` ABC +
  `MockFinancialDataProvider`)만 Mock이고, Knowledge Retrieval
  (`quick_company_scan.retrieve_knowledge_for_company()`)/Export
  (`export_quick_scan_report()`)는 전부 실동작이다. `AIProvider.quick_company_scan()`에
  `knowledge_excerpt` 파라미터를 하위호환 방식(기본값 `""`)으로 추가했다. 5개 테스트 +
  4개 테스트(Financial Provider).
- **Company Intelligence Score**: `scripts/company_intelligence_score.py` 신설 —
  Business Understanding/Market Position/Financial Visibility/Strategic
  Importance/Risk Visibility/Source Reliability/Knowledge Coverage 7개 하위 점수(각
  100점 만점, 완성도 기반 — 정확도가 아니라 "필드가 채워져 있는가"를 본다)와 그 평균인
  `overall`을 계산한다. Scenario 3(Investment Review)이 실행 시마다 계산해
  `COMPANY_SCAN_DB`에 함께 저장한다. 10개 테스트.
- **Executive Dashboard 6개 Widget 재구성**: "Dashboard는 HTML Viewer가 아니라
  Executive Dashboard가 되어야 한다" 지시에 따라 기존 소송·규제 특화 Widget 6종(Today's
  Change/Risk Tracker/Litigation/Regulation/Statistics/Timeline)을 전부 제거하고,
  Architect 지정 우선순위 그대로 6개 Widget(Today's Intelligence→Critical
  Risk→Future Opportunity→Quick Company Scan→Investment Review→Source Health)으로
  재구성했다. `scripts/pipeline/dashboard_feed.py`가 `COMPANY_SCAN_DB`와
  `config/sources.yaml`도 함께 읽도록 확장했다. Scenario 1/3이 같은
  `output/pilot_data/` 디렉터리를 공유하도록 통일해 하나의 Executive Dashboard가 두
  Scenario의 산출물을 함께 반영할 수 있게 했다. `render_generic_list()`가 `None`을
  문자열 "None"으로 렌더링하던 기존 버그(Round 4부터 존재, 이번에 처음 load-bearing이
  되며 발견)도 함께 고쳤다.
- **Knowledge Coverage 3종 추가**: 기존 8개 도메인 Coverage에 더해 Company
  Coverage(Company Registry 30개사 중 신뢰 가능한 Knowledge를 실제로 가진 비율,
  3.3%)/Country Coverage(Company Registry 국가 중 `active: true` Source가 있는 비율,
  22.2% — `country: multi` placeholder 2건은 둘 다 `active: false`라 실질 커버리지로
  세지 않음)/Industry Coverage(정확 문자열 매칭만 사용, 3.6%) 추가. Quality Gate의
  Evidence Quality 계산식은 기존 8개 도메인 평균 그대로 유지했다(조용히 바뀌지 않도록).
  RegistryManager를 재사용해 새 조회 로직을 만들지 않았다. 6개 테스트.
- **RegistryManager Validation/Integrity/Dependency Check**: "Registry는 조회만 하지
  않는다" 지시에 따라 `scripts/registries/validation.py` 신설 —
  `RegistryManager.validate()`(각 항목의 id 필드 존재 확인)/`check_integrity()`(Registry
  내부 id 중복 검사, 기존 `validate_config.py`가 다루지 않던 Company/Model/Prompt
  Registry의 공백을 메움)/`check_dependencies()`(`topics.yaml`의
  `related_lx_companies`, `pipeline/knowledge_retrieve.COMPANY_KNOWLEDGE_FILES`가
  Company Registry에 실재하는 company_id를 참조하는지 확인). `bootstrap_project.py`
  (Project Boot)가 `validate_all()`을 호출하도록 연결했다. 13개 테스트.
- **Technical Debt Registry**: `config/technical_debt_registry.yaml` 신설 — 코드
  감사로 실제 확인한 7건의 기술 부채(죽은 CSS, Knowledge 신뢰 판정 로직 3중 중복,
  가격표 placeholder, Scenario별 Dashboard 스냅샷 충돌 등)를 Severity/Priority/
  Estimated Time/Owner/Status 필드로 기록했다("실제 프로젝트 관리가 가능해야 한다"
  지시 반영). 새 Registry 어댑터를 만들지 않고 기존 `YAMLListRegistry`를 재사용해
  RegistryManager의 8번째 Registry(`technical_debt`)로 등록했다.
- **Quality Gate 4종 지표 추가**(전부 100점 만점): Architectural Stability("새로운
  Framework는 더 이상 만들지 않는다"는 제약을 `scripts/` 패키지 집합 비교로 직접
  계측), Operational Simplicity(5개 Scenario가 추가 인자 없이 단일 명령으로 끝까지
  실행되는지 실제 서브프로세스로 실측), Executive Usability(`sample_data.json` 기준
  실제 `build_html()` 호출로 6개 Widget 섹션이 전부 렌더링되는지 실측), AI Reasoning
  Readiness(`ClaudeProvider`가 `AIProvider`의 4개 추상 메서드 전부를 실제 Prompt
  Engine 경로까지 연결했는지 소스 코드로 확인 — Reasoning Quality와는 다른 축). 8개
  테스트.
- 전체 테스트 335개(Round 7) → 387개(+52개).

### Added — Architect Review Round 7 반영 (2026-08-07, 7차)

ChatGPT Architect Review Round 7 승인 및 반영("이번 라운드는 지금까지 중 가장 품질이
높았다" — Architecture A+/Code Quality A/Knowledge A/Scalability A+/Pilot Readiness A-).
최종 목표를 **Pilot Release Candidate(RC1)**로 명시했다 — 이후 라운드는 새 기능보다
Release 품질에 집중한다.

- **RegistryManager**: `scripts/registries/` 신설 — Company/Source/Model/Prompt/
  Workflow/Config/Storage 7개 Registry에 동일 Interface(`Registry.list_entries()`/
  `get()`/`count()`)를 씌우는 얇은 어댑터 계층. Architect 지시("새로운 Engine을 만드는
  것이 아니라 Registry 관리 방식을 통일한다")대로 각 Registry의 원본 파일/파싱 로직은
  전혀 바꾸지 않았다 — `quick_company_scan.py`가 `config/company_registry.yaml`을
  직접 읽는 기존 호출부도 그대로 유지된다. 17개 테스트.
- **Knowledge Coverage**: `scripts/knowledge_coverage.py` 신설 — Knowledge Quality를
  "문서 개수"가 아니라 "8개 도메인(Corporate/Market/Competitor/Government/
  Technology/Risk/Opportunity/Investment) Coverage"로 재정의했다. 키워드 유사
  매칭이 아니라 (파일, Section 번호) 명시적 목록으로 매핑한다 — 같은 단어("Manufacturing")
  가 `LX_HAUSYS_COMPANY_DNA.md`(기술 관점)와 `LX_HAUSYS_VALUE_CHAIN.md`(시장 관점)에서
  다른 의미로 쓰이기 때문이다. 신뢰 가능 여부 판정은 `knowledge_quality.py`의 기존
  로직을 재사용했다. 전체 평균 90.6%(Investment Coverage만 25% — `STRATEGY_PLAYBOOK.md`
  미착수가 원인, 회귀 감시용 테스트로 고정). 8개 테스트.
- **Company Registry 14→30개사**: LG전자/LG화학(2021년 LG그룹에서 계열 분리된 LX그룹과
  별개 법인임을 명시), 글로벌 유리 제조사 5개사(Saint-Gobain/AGC/NSG Group/Guardian
  Industries/Vitro), 글로벌 창호 제조사 6개사(Schüco/REHAU/Deceuninck/Andersen/Pella/
  Marvin), PPG + 30개사 목표 달성을 위해 Claude가 추가 선정한 Corning/Owens Corning
  (WebSearch로 티커 재확인, 추가 선정 사실을 코드 주석에 명시). 리서치는 서브에이전트로
  병렬 확인 후 반영. 4개 테스트.
- **Source Registry 필드 3종**: `config/sources.yaml` 11개 Source 전부에
  `estimated_update_delay`/`typical_reliability`/`historical_stability` 추가.
  `historical_stability`는 전부 "Pilot 자체 연동 이력 없음"으로 정직하게 표시했다
  (`feature_flags.real_network_calls=false`인 동안은 사실이다). 2개 테스트.
- **Scenario 5종 (TASK-017 변경)**: `scripts/demo_pilot.py`(Round 6의 "1개 통합 데모")를
  삭제하고 `scripts/scenarios/` 5개 독립 실행 스크립트로 전환 — 뉴스 분석/Quick Company
  Scan/Investment Review(Scenario 2를 내부 호출해 단독 실행 가능)/정부 정책 영향
  분석(신규)/경쟁사 변화 감지(신규). 정책 영향 분석을 위해 `AIProvider.
  analyze_policy_impact()` 신규 추상 메서드(+MockProvider/ClaudeProvider 구현체) 및
  `schemas/claude_output.schema.json`의 `policy_analysis_output` 정의를 추가해,
  Round 2부터 존재했지만 실제 호출자가 없었던 `prompts/policy_analysis.md`를 처음으로
  연결했다. 경쟁사 변화 감지는 스냅샷을 저장하고 직전 스냅샷과 비교하는 방식으로
  "변화 감지"를 정직하게 구현했다 — 최초 실행은 변화가 있었다고 지어내지 않고 "최초
  스냅샷"이라고 그대로 보고한다. 9개 테스트.
- **Quality Gate 5종 지표 추가**: Registry Quality(RegistryManager 구조+Registry
  Completion+Public Source Coverage 평균), Report Quality(Scenario 2/3를 실제로
  실행해 스키마 검증 실측 — 가정이 아니다), Evidence Quality(Knowledge Coverage+
  Registry Completion 평균), Reasoning Quality(**설계 proxy** — Mock Dependency
  100%인 현재 실제 출력 품질은 채점 불가, `risk_analysis`/`policy_analysis` 프롬프트가
  confidence/evidence/unknowns를 요구하는 설계인지만 확인하며 이를 코드 docstring에
  명시), Maintainability(`scripts/` 모듈 docstring 비율). 전부 100점 만점, 13개 테스트.
- **Connection Readiness**: `docs/CONNECTION_READINESS.md` 신설 — 실제 API 연결 없이
  Credential 체크리스트(시스템별), 환경변수 목록, OAuth 흐름 안내, Connection Test
  Plan(8단계, 위험이 낮은 순), Rollback Plan(Feature Flag를 되돌리는 것이 유일하고
  가장 빠른 킬스위치)을 문서화했다. `.env.example`에 그동안 코드는 참조하지만 예시
  파일에 없었던 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`/`LCIP_TEST_EMAIL_RECIPIENT`/
  모델 3종 환경변수를 보강했다.
- Investment Review Engine은 Round 5와 동일하게 Comparable 기반만 유지(DCF/LBO/
  Option은 계속 Enterprise Backlog) — 이번 라운드는 변경 없이 확인만 했다.
- 테스트: 총 **335개 테스트 전부 PASS**(Round 6: 284개 → +51개).
- 문서: `CLAUDE.md`(Round 6/7 절 신설, `demo_mvp.py`/`demo_pilot.py` 관련 서술을
  현재 상태로 갱신), `PROJECT_STATUS.md`/`TODO.md`(Round 7 반영으로 전면 갱신),
  `docs/CONNECTION_READINESS.md`(신규).

### Notes

- 이번 라운드도 외부 API를 전혀 호출하지 않았다 — `config/feature_flags.yaml`의 4개
  플래그가 전부 `false`인 한, Scenario 4가 새로 연결한 `analyze_policy_impact()`를
  포함해 모든 실제 호출 경로가 안전하게 도달 불가능한 상태로 남는다.
- Reasoning Quality(100점)는 "실제 추론 결과가 우수하다"는 뜻이 아니라 "프롬프트가
  추론 근거를 요구하도록 설계되어 있다"는 뜻이다 — 다음 라운드 이후 실제 API 연결이
  시작되면 이 지표의 정의 자체를 재검토해야 한다.
- Company Registry의 여러 필드(products/value_chain/official_website/
  primary_disclosure_source)는 여전히 TODO다 — 30개사로 확대된 만큼 리서치 부담도
  늘었다.

### Added — Architect Review Round 6 반영 (2026-08-05, 6차)

ChatGPT Architect Review Round 6 승인 및 반영. "Engine Development"에서 "Working
Product"로 방향을 전환 — 새 Engine/Framework/Layer 추가를 절대 금지하고, 실제 데이터를
사용하는 Pilot 완성에 집중했다. 이번 라운드 집중사항(1. 중복 구조 제거, 2. 불필요한
추상화 제거, 3. Pilot에서 실제 사용하지 않는 코드 표시)도 함께 반영했다.

- **TASK-K01 Knowledge Population**: `knowledge/LX_HAUSYS_COMPANY_DNA.md` →
  `LX_HAUSYS_VALUE_CHAIN.md` → `LX_HOLDINGS_CONTEXT.md` → `GROUP_RISK_MAP.md` →
  `GROUP_OPPORTUNITY_MAP.md` 5개 문서를 WebSearch로 확인한 실제 공개정보로 전면
  리라이트(모든 문장에 Source URL/Reference Date/Confidence). LX Hausys의 named
  lawsuit 피고 여부처럼 확인되지 않은 사실은 명확히 "미확인"으로 분리했다. Knowledge
  Quality Score 평균 25% → **95.8%**.
- **TASK-K02 Company Registry**: `config/company_registry.yaml`을 1개사에서
  14개사(LX Group 6/국내 경쟁사 2/해외 엔지니어드스톤 경쟁사 4/일본 경쟁사 2)로 확대.
  각 회사는 Company ID/Ticker/Country/Industry/Products/Value Chain/Official
  Website/Primary Disclosure Source를 갖는다. 미확인 필드는 `null`+TODO 주석으로 정직하게
  남겼다(임의 기재 금지 원칙 유지).
- **TASK-K03 Source Registry**: `config/sources.yaml`을 4개에서 11개 Source(Google
  RSS/Naver/DART/KRX/SEC EDGAR/EDINET/SEDAR+/Companies House/정부 RSS/기업 IR)로
  확대. `authentication`/`rate_limit` 필드 신설(예: SEC EDGAR는 API Key 불필요·User-Agent
  헤더 필수·초당 10 requests로 확인). 세분화 점수는 기존 `source_priority.py`를 그대로
  재사용해 중복 필드를 만들지 않았다.
- **Feature Flag + TASK-010 실제 RSS Parser**: `config/feature_flags.yaml`(신규,
  4개 스위치 전부 `false`) + `scripts/feature_flags.py`. `GoogleRSSAdapter.enabled`
  기본값이 하드코딩 `False`에서 이 전역 플래그를 따르도록 전환 — 개별 `enabled=True` 인자는
  여전히 우선한다.
- **TASK-009 실제 ClaudeProvider + Provider Factory**: `ClaudeProvider._call_anthropic()`이
  `anthropic` SDK로 실제 Messages API를 호출하는 코드로 교체됐다(모델은 여전히
  `claude_client.get_model_name()`으로 조회). `feature_flags.claude_api_enabled=False`인
  한 SDK import조차 하지 않고 `NotImplementedError`로 멈춘다(2중 게이트: `self.enabled`
  + feature flag). `scripts/providers/factory.py:get_default_provider()` 신설 —
  `ANTHROPIC_API_KEY` 존재 + flag 둘 다 참일 때만 `ClaudeProvider(enabled=True)`, 아니면
  항상 `MockProvider()`.
- **TASK-017 데모 통합(2→1)**: `scripts/demo_pilot.py` 신설, 기존 `demo_mvp.py`/
  `demo_quick_scan.py` 삭제. 뉴스수집→Rule Filter→Knowledge Retrieval→Claude
  Analysis→INTELLIGENCE_DB→Dashboard→Quick Company Scan→Investment Review→Email
  Preview→Telegram Preview를 한 명령으로 실행한다.
- **Quality Gate**: `scripts/quality_gate.py` 신설 — Coverage 대신 품질을 측정한다.
  Knowledge Quality Score(95.8%)/Registry Completion(48.8%, 참고 지표)/Public Source
  Coverage(100%)/Source Freshness(등록 Source 중 `active` 비율, 18.2%)/Mock
  Dependency(feature flag가 false인 비율, 100%)/Pilot Operational Readiness(구조적
  점검 7개 항목 통과율, 100%) — 전체 테스트 스위트를 서브프로세스로 실제 실행해 판정하며,
  재귀 실행을 피하기 위해 `run_tests` 인자로 제어한다.
- **중복/데드코드 감사 및 정리**: `scripts/pipeline/store.py`(하위호환 wrapper — 실제
  호출자가 자기 자신의 단위 테스트뿐이었음)를 삭제하고 `tests/test_pipeline.py`의 관련
  테스트 2건도 제거(동일 커버리지가 `tests/test_storage.py`에 이미 있음).
  `claude_client.build_cached_messages()`(Round 5부터 `prompt_engine.PromptBuilder`로
  대체되어 실제 호출자가 없었음)와 그 테스트 1건 삭제. `build_dashboard.py`가 JSON 파일을
  직접 `json.loads()`하던 중복 구현을 `dashboard_data_provider.StaticJSONDataProvider`
  재사용으로 교체. `scripts/providers/future_providers.py`/
  `scripts/adapters/future_adapters.py`/`scripts/storage/future_storage.py`(Round 4/5가
  승인한 확장 지점 stub)에는 "Pilot 데모가 호출하지 않는다"는 감사 표시를 코드 주석으로
  남겼다 — 단위 테스트로만 계약을 검증하는 의도된 설계이므로 삭제 대상이 아니다.
  `config/company_registry.yaml`의 "LX Group (8개사)" 주석 오류(실제 6개사)도 함께 수정.
- 테스트: 신규 `test_feature_flags.py`(5), `test_source_registry.py`(6),
  `test_quality_gate.py`(14) + 기존 파일 확장(`test_adapters.py` +2, `test_providers.py`
  +8, `test_quick_company_scan.py` +5) — 데드코드 제거로 3건 감소. 총
  **284개 테스트 전부 PASS**(Round 5: 265개).
- 문서: `CLAUDE.md`(Storage Backend 항목에 Round 6 삭제 내역 반영),
  `PROJECT_STATUS.md`/`TODO.md`(Round 6 반영으로 전면 갱신).

### Notes

- 이번 라운드도 외부 API를 전혀 호출하지 않았다 — `config/feature_flags.yaml`의 4개
  플래그가 전부 `false`인 한, 새로 작성된 실제 호출 코드(`ClaudeProvider._call_anthropic`,
  `GoogleRSSAdapter.collect`)는 안전하게 도달 불가능한 상태로 남는다.
- Company Registry의 여러 필드(products/value_chain/official_website/
  primary_disclosure_source)는 여전히 TODO다 — Round 6는 "구조를 Pilot 수준으로 확장"이
  목표였고, 전 필드 리서치 완결은 다음 라운드 과제다.

### Added — Architect Review Round 5 반영 (2026-08-05, 5차)

ChatGPT Architect Review Round 5 승인 및 반영. "Pilot을 실제 사용할 수 있는 방향으로
고도화"가 목표 — Round 4의 Architecture Layer(Provider/Adapter/Pipeline/Widget)는
안정적이라고 판단해 그대로 두고, 그 위에 4개 하위 엔진을 추가했다. Quick Company Scan을
Pilot의 첫 번째 실제 서비스로 승격하고 Investment Review Engine과 연결했다. 새 Framework
문서는 여전히 추가하지 않았고, 외부 API 실제 연결도 계속 시작하지 않았다.

- **TASK-010A Storage Backend**: `scripts/storage/` — `StorageBackend`(추상) →
  `LocalJSONLStorage`(실동작, Pilot 기본값) / `GoogleSheetsStorage`(구조만,
  `enabled=False`, ClaudeProvider와 동일한 2중 안전장치 패턴) / `FutureDatabaseStorage`
  (stub). `pipeline/store.py`는 하위호환 래퍼로 남기고 내부적으로 `LocalJSONLStorage`에
  위임한다. `demo_mvp.py`/`test_mvp_integration.py`는 `StorageBackend`를 직접 사용하도록
  전환해 "Pipeline은 StorageBackend만 참조한다"를 실제로 만족시켰다. 10개 테스트.
- **Source Reliability Score**: `config/source_reliability.yaml`(정부/기업IR/DART/SEC=5,
  로이터=4, Google RSS=3, 블로그=2, SNS=1) + `scripts/source_priority.py`
  (`score_for_source_type()`, `resolve_conflict()`로 동일 사실 충돌 시 높은 점수 근거
  우선). 기존 `reliability_grade`(A/B/C, Source 단위)와는 별도 축. 18개 테스트.
- **TASK-009B Knowledge Retrieval Engine**: `scripts/knowledge_engine.py` —
  knowledge/*.md를 Section 단위로 파싱해 `search_by_section/company/topic/
  source_priority/confidence/last_verified()`로 검색 가능하게 한다. 부수 효과로
  `scripts/knowledge_quality.py`가 4줄 분리 메타데이터 서식(`LX_HAUSYS_COMPANY_DNA.md`
  등)을 지원하지 않아 실제 값이 있어도 항상 "메타데이터 없음"으로 오판정하던 버그를
  발견해 함께 고쳤다 — 두 모듈이 같은 파서(`extract_section_metadata()`)를 공유한다.
  14개 테스트(회귀 테스트 1건 포함).
- **TASK-009A Prompt Engine**: `scripts/prompt_engine/` — `PromptTemplate`(prompts/*.md
  로드) → `PromptBuilder`(Static/Knowledge/Source/Dynamic/Context 5블록 조립) →
  `PromptValidator` → `PromptCache`(같은 프로세스 내 Static Block 재조립 방지).
  `ClaudeProvider`가 `claude_client.build_cached_messages()` 대신 이 엔진을 쓰도록
  전환 — `lx_context_excerpt`는 Knowledge Block으로, 기사 출처의 Source Reliability
  Score는 Source Block으로 분리되었다(`prompts/risk_analysis.md` v0.3.0). 10개 테스트
  + Provider 쪽 2개.
- **TASK-012A Dashboard Data Provider**: `scripts/dashboard_data_provider.py` —
  `DashboardDataProvider`(추상) → `StaticJSONDataProvider`/`PipelineDashboardDataProvider`
  (`StorageBackend` 연동). `Widget`을 `get_data(data)`(구조화 데이터, HTML 아님)와
  `render_html(widget_data)`(순수 렌더러)로 분리 — `render()`는 하위호환용으로 둘을
  조합한 편의 메서드로만 남았다. `demo_mvp.py`가 `PipelineDashboardDataProvider`를
  거치도록 전환. 8개 테스트.
- **Quick Company Scan 실제 서비스 승격**: `scripts/quick_company_scan.py` +
  `config/company_registry.yaml`(회사명/별칭/Ticker/DART 회사명 → company_id 정규화,
  임의로 회사를 지어내지 않고 미등록은 `resolved=False`로 정직하게 처리) — 입력 →
  `resolve_company_input()` → `select_sources_for_company()`(국가/DART 등록 여부로 자동
  선택) → `AIProvider.quick_company_scan()`(신규 추상 메서드, `MockProvider`/
  `ClaudeProvider`/미래 Provider 전부 구현) → `build_quick_report()`(Core 스키마 검증) →
  `build_investment_review_input()`. 12개 테스트 + Provider 쪽 2개.
- **Investment Review Engine**: `scripts/investment_review.py` +
  `schemas/investment_review.schema.json` — Comparable(Peer EV/EBITDA·PER·PBR) 기반
  Valuation만 계산(`compute_peer_average()`, `build_estimated_valuation()`은 대상기업
  실적 미확인 시 금액 범위 대신 Peer 배수만 제시) — **DCF는 Enterprise Backlog**(Pilot
  범위 아님, Architect Review Round 5 명시). `detect_deal_killers()`가 risk_assessment
  키워드(소송/제재/형사/파산/상장폐지/회계부정)를 찾으면 다른 조건과 무관하게
  `recommendation.signal = decline_deal_killer_found`로 덮어쓴다. 최종 투자판단이 아닌
  스크리닝 신호까지만 제공(`knowledge/INVESTMENT_FRAMEWORK.md`와 동일 원칙, 해당 문서의
  "Pilot에 연결 안 됨" 문구를 최신 상태로 수정). 14개 테스트.
- **Technical Debt 4건 제거**(Architect Review Round 4 자체 제안 승인):
  1) `claude_client.call_claude_mocked()`/`ClaudeUsage`/`ClaudeCallResult` 제거 —
     `providers.mock_provider.MockProvider`로 완전히 대체되어 있었다.
  2) `config/model_pricing.yaml`의 키(`placeholder_low_cost_model` 등)를
     `config/model_registry.yaml`의 tier 키(classification/deep_analysis/future)와
     통일해 `cost_tracking.py`의 `TIER_TO_PRICING_KEY` 이중 매핑 테이블을 제거.
  3) `dashboard_widgets.py`의 `RegulationWidget(...)` 3회 반복 생성을
     `_REGULATION_WIDGET_CONFIGS` 목록 기반 생성으로 정리.
  4) `scripts/health_tracking.py`(Adapter 연동)를 `scripts/source_health_check.py`
     (판정 로직)로 병합 — 파일명은 `docs/03_BUILD_SPECIFICATION.md` 원문이 지정한
     `source_health_check.py`를 그대로 유지했다. `tests/test_health_tracking.py`도
     `tests/test_source_health.py`로 병합.
- 테스트: 신규 91건 추가, 기존 148건과 합쳐 총 **239개 테스트 전부 PASS**.
- 문서: `CLAUDE.md`/`TODO.md`/`PROJECT_STATUS.md` 갱신, `knowledge/INVESTMENT_FRAMEWORK.md`
  §4의 오래된 "Pilot에 연결 안 됨" 서술을 현재 상태로 수정.

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
