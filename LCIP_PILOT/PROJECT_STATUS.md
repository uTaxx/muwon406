# Project Status

최종 갱신: 2026-08-08 (Architect Review Round 12 반영)

## 요약

TASK-001~007 → Round 2~11(Knowledge/Provider/Registry/Coverage/Scenario화/RC1 정의/
Data Sprint/UX Sprint) → **Round 12("RC1 승인 + RC2 준비") 반영** 완료. Architect는
"Round 11 결과를 승인한다. LCIP Pilot RC1을 공식 승인한다. 현재부터 RC1은
동결(Frozen)하고, 새로운 기능·Framework·Engine·Registry·Layer를 추가하지 않는다.
다음 단계는 RC2 준비다"라고 선언했다. 이번 Round는 3개 항목(TD-006 해결/Reference
Library MVP/RC2 Connection Plan)만 수행했다.

**LCIP Pilot RC1이 공식 승인되었다** — ADR-010이 정의한 구조적 요건(Round 8)과
콘텐츠 요건(Round 10 TOP10 완성)에 이어 사용성 요건(Round 11)까지 Architect가
검토를 마쳤다. 이후 모든 개발은 "이 기능이 Pilot의 실제 사용자 검증에 필요한가?"
질문을 통과해야 하며, RC2(실제 외부 API 연결)가 다음 목표다.

## Round 12 TASK 3개 처리 결과

| 순위 | 항목 | 상태 | 핵심 내용 |
|---|---|---|---|
| 1 | TD-006 Dashboard 자동 갱신 | ✅ 완료 | `scenario_3_investment_review.py`가 Scenario 1과 동일한 Dashboard Builder를 재사용해 Export 다음 단계로 `dashboard.html`을 직접 갱신. News Intelligence 데이터 보존, `_dedupe_most_recent_by()`로 같은 회사 반복 스캔 시 무한 중복 방지 |
| 2 | Reference Library MVP | ✅ 완료 | `reference_library/{inbox,active,archive,index}` + `scripts/reference_library.py` 신설(Architect 명시적 예외 승인). Knowledge Engine 비대체, Embedding/RAG 없음. Scenario 1/2/3이 "참조 근거" 절 표시, Home Dashboard에 새 Widget 없이 6번째 카드 추가 |
| 3 | RC2 Connection Execution Plan | ✅ 완료 | `docs/RC2_CONNECTION_CHECKLIST.md` 신설 — A(사용자)/B(Claude)/C(공동확인) 역할 분담, Credential 12개 항목 표, RC2 연결 우선순위 8단계 반영 |

## 테스트 결과

```text
$ pytest tests/ -q                                              -> 전부 PASS (438개 테스트, Round 11: 409개 → +29개)
$ python scripts/validate_config.py                             -> PASS
$ python scripts/secret_scan.py                                  -> PASS
$ python scripts/bootstrap_project.py --dry-run                   -> PASS (Registry 8개 전체 검증 통과)
$ python scripts/scenarios/scenario_3_investment_review.py "LX Hausys"  -> PASS (Home Dashboard 자동 갱신 + 참조 근거 절 확인)
```

## Round 12에서 새로 생성/수정된 파일

**신규**: `scripts/reference_library.py`, `schemas/reference_metadata.schema.json`,
`docs/RC2_CONNECTION_CHECKLIST.md`, `tests/test_reference_library.py`,
`reference_library/{inbox,active,archive,index}/.gitkeep`

**수정**
- `scripts/scenarios/scenario_3_investment_review.py`: Export 다음 단계로 Home
  Dashboard 갱신 추가, Reference Library 조회 결과(`reference_entries`)를 Export/
  COMPANY_SCAN_DB(`reference_ids_used`)로 전달.
- `scripts/scenarios/scenario_2_quick_company_scan.py`: Reference Library 조회
  단계 추가(`list_active_references_for_company()`).
- `scripts/scenarios/scenario_1_news_analysis.py`: Topic 관련 회사 기준 Reference
  Library 조회 단계 추가.
- `scripts/quick_company_scan.py`: Markdown/Executive Report에 "참조 근거" 절 추가.
- `scripts/pipeline/dashboard_feed.py`: `_dedupe_most_recent_by()`,
  `_reference_library_row()`, `reference_library_rows` 키 추가.
- `scripts/dashboard_data_provider.py`: `PipelineDashboardDataProvider`가
  `reference_library_summary()`를 조회해 전달(유일한 파일시스템 접근 지점).
- `dashboard/template.html`/`sample_data.json`: Home Dashboard 6번째 카드
  "Reference Library" 추가.
- `.gitignore`: `reference_library/` 실제 파일/색인은 Git에서 제외(구조만 유지).
- `docs/CONNECTION_READINESS.md`: §5에 Round 12 우선순위로 대체됐다는 포인터 추가.
- 테스트: `test_scenarios.py`(+7)/`test_dashboard_feed.py`(+4)/
  `test_reference_library.py`(신규 +14)/`test_dashboard.py`(+2)/
  `test_dashboard_data_provider.py`(+2) 총 29건 추가.

## Round 11에서 새로 생성/수정된 파일 (과거 기록)

**신규**: `docs/PILOT_DEMO_PACKAGE.md`, `docs/USER_GUIDE.md`

**수정**
- `dashboard/template.html`: `<section id="home">` 신설(5개 카드).
- `dashboard/styles.css`: `.lcip-home-grid`/`.lcip-home-command` 추가 — 기존
  미사용 `.lcip-today-change` 카드 스타일을 재사용.
- `scripts/build_dashboard.py`: `_render_common_tokens()`에 `HOME_*` 토큰 4개 추가.
- `scripts/pipeline/dashboard_feed.py`: `_news_row()`/`recent_news` 키 추가 —
  기존에 받기만 하고 안 쓰던 `articles` 인자를 처음 활용.
- `dashboard/sample_data.json`: `recent_news` 예시 1건 추가.
- `scripts/scenarios/scenario_3_investment_review.py`: `main()`에 "결과 요약"
  출력 블록 추가.
- `scripts/quick_company_scan.py`: `build_executive_report_html()` 신설,
  `export_quick_scan_report()`가 반환하는 dict에 `executive_report_path` 추가.
- 테스트: `test_dashboard.py`(+2)/`test_dashboard_feed.py`(+2)/`test_scenarios.py`(+1)/
  `test_quick_company_scan.py`(+2) 총 7건 추가.

## Round 10에서 새로 생성/수정된 파일 (과거 기록)

**신규 Knowledge 문서(9건, `knowledge/`)**: `KCC_COMPANY_PROFILE.md`,
`HANSSEM_COMPANY_PROFILE.md`, `CAESARSTONE_COMPANY_PROFILE.md`,
`COSENTINO_COMPANY_PROFILE.md`, `SHAW_INDUSTRIES_COMPANY_PROFILE.md`,
`LIXIL_COMPANY_PROFILE.md`, `YKK_AP_COMPANY_PROFILE.md`, `SCHUCO_COMPANY_PROFILE.md`,
`SAINT_GOBAIN_COMPANY_PROFILE.md` — 전부 WebSearch로 확인한 실제 사실 + 원문 URL,
16계층 Taxonomy 준수, §10 Risk 항목에 TOP-0001(실리코시스) 소송 노출 여부를 "확인됨"/
"확인 안 됨(무혐의 확정 아님)"으로 정직하게 구분 기록.

**중대 수정**
- `scripts/pipeline/knowledge_retrieve.py`: `COMPANY_KNOWLEDGE_FILES`에 9개사 매핑
  추가(각 회사는 자기 프로필 문서 1개만 참조 — LX 그룹 맥락과 섞이지 않도록).
- `config/company_registry.yaml`: 9개사의 `products`/`value_chain`/일부
  `official_website` 필드를 TODO에서 실제 리서치 값으로 갱신(검증 못한 필드는 계속
  TODO/null 유지).
- `scripts/financial_provider.py`: `MockFinancialDataProvider`가 항상 반환하던
  고정 "Peer A/B (예시)"를 삭제하고, 회사별 실제 Comparable Peer 그룹(`_PEER_COMPANY_IDS`)
  + 실제 확인된 배수(`_KNOWN_MULTIPLES`, 미확인은 `None`)로 교체. 자기 자신은 자신의
  Peer 목록에서 제외.
- `scripts/quick_company_scan.py`: Export의 Comparable Peer 표에서 `None` 배수를
  "-"로 표시하도록 수정(가독성), "전부 예시 데이터" 문구를 "회사명은 실제 기업"으로
  정정.
- `dashboard/styles.css`: Technical Debt TD-001(죽은 CSS 5개 클래스,
  `.lcip-trend-chart`/`.lcip-stat-*`) 삭제 — Round 8 Widget 재구성 이후 미사용 상태였다.
- `config/technical_debt_registry.yaml`: TD-001 상태를 `resolved`로 갱신.
- 테스트: `test_financial_provider.py` 전면 재작성(9개), `test_knowledge_coverage.py`/
  `test_company_intelligence_score.py`/`test_quick_company_scan.py`의 "Knowledge
  없는 회사" 회귀 테스트 기준을 CAESARSTONE(이제 Knowledge 보유)에서 WILSONART(여전히
  미보유)로 교체.

## 알려진 설계 결정 이력 (전체, 상세는 docs/04_DATA_AND_CONFIG_SCHEMA.md §1/§5, 각 ADR)

- ADR-006/007/008/009/010: 문서 우선순위 / n8n 통합 / Workflow ID 정책 / Workflow
  생명주기 / Release Policy(RC1 정의)
- Round 2~12의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록
- **RC1 공식 승인(Round 12)**: ADR-010의 구조적 요건(Round 8)+콘텐츠 요건(Round 10)+
  사용성 요건(Round 11)을 모두 충족한 것으로 Architect가 승인했다. RC1은 이제
  동결(Frozen) 상태이며, 새로운 기능/Framework/Engine/Registry/Layer는 추가하지
  않는다(Round 12가 명시적으로 예외 승인한 Reference Library MVP는 제외).

## 남은 사용자 작업 / 알려진 한계

`TODO.md` 참고 — Round 12도 여전히 Mock/dry-run 기반이며 실제 외부 API 호출은
시작하지 않았다(RC1 동결, RC2는 다음 단계). Round 12가 새로 확인한 한계:
- **Reference Library 승격은 사용자가 직접 파일을 옮겨야 한다** — Pilot이 사용자
  파일을 임의로 이동시키지 않는다(안전 원칙)는 설계상, `inbox/`→`active/` 이동은
  사용자가 직접 한다. 자동 분류(문서유형 추정 등)는 이번 MVP 범위 밖이다.
- **RC2 실제 연결은 아직 시작 전** — `docs/RC2_CONNECTION_CHECKLIST.md`의 Credential
  12개 항목이 전부 미준비 상태다. 사용자가 "N번 항목 준비 완료"를 알려줘야 다음
  Round에서 순서대로(§2, Claude API부터) 실제 연결을 시작할 수 있다.

Round 11이 확인한 한계(계속 유효):
- **Home Dashboard의 "실행" 카드는 클릭할 수 없다** — Pilot이 서버 없는 정적
  HTML+CLI 구조라 명령어 텍스트로만 안내한다. 실제 클릭 실행이 필요하면 RC2 이후
  경량 로컬 서버 도입을 Architect 승인 사항으로 검토해야 한다.
- **Executive Report(HTML)는 PDF가 아니다** — 이번 Sprint 지시("PDF는 구현하지
  않는다")대로 HTML만 지원한다. 브라우저 인쇄 기능으로 PDF 변환은 가능하다.

사용자 검증 결과 확인된 기존 핵심 한계(Round 10 이전, 계속 유효):
- **Company Registry 30개사 중 10개사만 실제 Knowledge 보유** — TOP10 완성 이후에도
  나머지 20개사(LG전자·LG화학, AGC·NSG·Guardian·Vitro, Rehau·Deceuninck·Andersen·
  Pella·Marvin, PPG·Corning·Owens Corning, Wilsonart 등)는 여전히 Mock이다. 다음
  Data Sprint의 후보군이다.
- **Investment Review 배수(EV/EBITDA·PER·PBR)가 부분적으로만 채워짐** — 비상장
  기업(Cosentino/YKK AP/Schüco/Shaw)은 공개 배수 자체가 없어 구조적으로 `None`이
  유지된다. 상장사도 일부 배수는 이번 세션 네트워크 제한으로 재무데이터 사이트 직접
  대조를 못해 검색 스니펫 기반 저신뢰 값으로 남아 있다(각 Knowledge 문서에 명시).
- **뉴스 분석(risk_analysis)/정책 분석은 여전히 고정 mock 문구** — "사람이 다시 읽지
  않아도 될 정도"는 RC2(실제 Claude 연동) 이후에나 가능하며, Round 10도 실제 API
  호출을 금지했다.
- `docs/CONNECTION_READINESS.md`의 Credential 체크리스트대로 Claude API Key/모델 ID
  3종/Google/n8n/Gmail/Telegram 계정을 준비하고 `config/feature_flags.yaml`을 켜야
  "실제 동작"(RC2)으로 전환된다.
