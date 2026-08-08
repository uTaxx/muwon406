# Project Status

최종 갱신: 2026-08-08 (뉴스 수집 실체화 — n8n 네이티브 재구현 + Keyword Group + 중요도 판정)

## 요약

TASK-001~007 → Round 2~12(Knowledge/Provider/Registry/Coverage/Scenario화/RC1 승인/
UX Sprint/RC2 준비) → **Round 13("RC2 실체화") 반영** 완료. Architect는 "LCIP는
설계 단계를 종료하고 RC2(실체화 단계)로 전환한다. 지금부터는 새로운 기능을 추가하지
않는다. Pilot MVP를 실제 사용할 수 있는 상태로 만드는 것이 최우선이다"라고 선언하며,
Claude가 독립적으로 수행 가능한 코드 작업은 승인 없이 계속 진행하라는 새 개발 원칙을
제시했다.

**이미 설계됐지만 `NotImplementedError`로 막혀 있던 실제 외부 연결 코드를 전부
완성했다** — Google Drive 폴더 생성, Google Sheets 탭 생성 + Storage 읽기/쓰기,
n8n 워크플로우 배포, Gmail/Telegram 실제 발송. Credential만 입력하면 즉시 동작한다
(현재는 전부 미입력 상태라 실제 호출은 여전히 0건). DART/Naver Adapter는 추가 설계
결정(회사명→corp_code 매핑 등)이 필요해 이번 Round에서는 보류했다.

## 뉴스 수집 실체화 (2026-08-08)

사용자 지시 "N8N 적용해서 뉴스 수집하는 것부터 실체화 하자"에 따라 Plan Mode로
설계 후 실행했다. 핵심 결정 3가지(사용자 승인): (1) n8n Cloud가 이 코드저장소를
직접 실행할 수 없어 Python 파이프라인 로직을 n8n Code/HTTP 노드로 네이티브
재구현, (2) 키워드 그룹/AI지침/수집주기 편집은 정적 HTML 대시보드가 아니라 Google
Sheets(KEYWORD_GROUPS 탭)에서, (3) 이번 라운드 소스 범위는 Google News+Naver
News만(DART/정부보도자료 제외).

- **완료**: Keyword Group 스키마(Sheets+로컬 YAML), Naver 실제 어댑터,
  `importance_level`(긴급/중요/참고) 신설, 실제 배치 파이프라인
  `scripts/run_news_collection.py`, n8n WF-P01 네이티브 재구현(cron 3개, Naver
  연동, AI Analyze/Notification 활성화), Home Dashboard "설정 현황" 카드(읽기
  전용).
- **알려진 한계**(TD-008): n8n JS 로직은 Python을 수동 이식한 것이라 실제 n8n
  인스턴스 미검증, 프롬프트 변경 시 수동 동기화 필요, 분석 대상 0건 실행에서
  다이제스트가 발송 안 될 수 있음, 수집 주기는 Sheets가 아니라 n8n 노드 재배포로만
  변경 가능.
- **다음 Blocker**: `N8N_BASE_URL`(실제 n8n 배포), `GOOGLE_SHEETS_MASTER_
  SPREADSHEET_ID`(실제 Sheets 연동) 둘 다 여전히 미확보 — 확보되면
  `scripts/n8n_deploy.py --apply`/`create_google_sheets.py --apply`로 다음 단계
  진행 가능.
- 전체 테스트 487개, 전부 PASS. 외부 API 실제 호출 0건(`feature_flags.yaml` 전부
  false 유지).

## Round 13 이어서: Credential 반영 + 모델 티어 결정

사용자가 Google Drive Sheet("Activate" 탭 한정)에서 실제 Credential을 제공했다.
`.env`(Git 미포함)에 Anthropic/Google OAuth/n8n API Key/Telegram/DART/Naver
6개 항목을 반영했고(값은 어디에도 노출하지 않음), Claude 모델 3개 티어는
WHY/WHAT/HOW 질문에 사용자가 "분류=Haiku, 심층분석/미래준비=Sonnet"으로 답해
`config/model_registry.yaml`/`.env`에 반영했다.

## Round 13 이어서: Claude API 최초 실제 연결 검증

Priority 1 질문("Flag를 지금 켤까?")에 사용자가 "Claude API만 켜서 최소 비용
검증"으로 답해, LCIP 역사상 최초로 실제 Anthropic API를 호출했다(`scripts/
verify_claude_connection.py`). 연결·인증·모델 호출은 전부 정상 확인(비용
$0.01 미만). 이 과정에서 Haiku 4.5가 응답을 마크다운 JSON 코드펜스로 감싸는
경우 파싱이 항상 실패하던 실제 버그를 발견해 수정했다(`ClaudeProvider.
_call_anthropic`). 검증 후에는 `feature_flags.yaml`의 `claude_api_enabled`를
다시 `false`로 되돌렸다 — "1회 검증"과 "Scenario가 상시 실제 비용을 발생시키는
전환"은 별개의 결정이라고 판단했다. Flag를 계속 켜 둘지는 다음 Priority 1
질문으로 남겼다. 또한 검증 중 `intelligence_categories` enum에 "산업안전"에
정확히 대응하는 값이 없다는 Taxonomy 데이터 품질 이슈를 발견했다(범위 밖이라
이번 Round에서는 고치지 않음, 다음 Round 후보로 기록).

## Round 13 실체화 처리 결과

| 우선순위 | 항목 | 상태 | 핵심 내용 |
|---|---|---|---|
| 1 | Claude API | 코드 완료(기존) | `ClaudeProvider._call_anthropic()` — Round 6부터 완전 구현, Credential 대기만 |
| 2 | Google Drive/Sheets | ✅ 코드 완료 | `google_auth.py` 신설(OAuth Desktop/Service Account 공용), Drive 폴더 생성 멱등적 구현, Sheets 탭 생성 + `GoogleSheetsStorage` 실제 읽기/쓰기 |
| 3 | Google News RSS | 코드 완료(기존) | `GoogleRSSAdapter` — Round 6부터 완전 구현 |
| 4 | DART | ⏸ 보류 | 어댑터 stub 그대로 — 회사명→corp_code 매핑 설계 필요 |
| 5 | n8n API | ✅ 코드 완료 | `n8n_deploy.py`가 이름 매칭으로 갱신/생성(삭제 없음). 실제 n8n 인스턴스로 미검증 — 주석에 명시 |
| 6 | Gmail | ✅ 코드 완료 | `EmailNotifier`가 Gmail API로 실제 발송(2중 안전장치 유지) |
| 7 | Telegram | ✅ 코드 완료 | `TelegramNotifier`가 Bot API로 실제 발송(2중 안전장치 유지) |
| 8 | Naver News | ⏸ 보류 | 어댑터 stub 그대로 |

## 테스트 결과

```text
$ pytest tests/ -q                                              -> 전부 PASS (449개 테스트, Round 12: 438개 → +11개)
$ python scripts/validate_config.py                             -> PASS
$ python scripts/secret_scan.py                                  -> PASS
$ python scripts/bootstrap_project.py --dry-run                   -> PASS (Registry 8개 전체 검증 통과)
```

## Round 13에서 새로 생성/수정된 파일

**신규**: `scripts/google_auth.py`, `tests/test_n8n_deploy.py`,
`tests/test_create_drive_structure.py`, `tests/test_create_google_sheets.py`

**수정**
- `scripts/create_drive_structure.py`: `apply_plan()` 실제 Drive API 호출 완성
  (멱등적 폴더 생성).
- `scripts/create_google_sheets.py`: `apply_plan()` 실제 Sheets API 호출 완성
  (gspread, 누락 탭만 생성), `--auth-mode` 옵션 추가.
- `scripts/storage/google_sheets_storage.py`: `append()`/`load_all()` 실제 구현
  (gspread 경유, `client_factory` 주입 지원).
- `scripts/n8n_deploy.py`: `apply_deploy()` 실제 n8n Public API 호출 완성(이름
  매칭 갱신/생성, 삭제 없음).
- `scripts/notifiers.py`: `EmailNotifier`(Gmail API)/`TelegramNotifier`(Bot API)
  실제 발송 경로 완성.
- `requirements.txt`: `google-api-python-client`/`google-auth`/
  `google-auth-oauthlib`/`gspread` 추가.
- `docs/GOOGLE_DRIVE_SETUP.md`/`docs/GOOGLE_SHEETS_SETUP.md`/
  `docs/RC2_CONNECTION_CHECKLIST.md`: apply 로직이 실제로 구현됐음을 반영.
- 테스트: `test_storage.py`(+1)/`test_notifiers.py`(+3)/`test_n8n_deploy.py`
  (신규 +3)/`test_create_drive_structure.py`(신규 +2)/`test_create_google_sheets.py`
  (신규 +2) 총 11건 추가.

## Round 12에서 새로 생성/수정된 파일 (과거 기록)

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

`TODO.md` 참고 — Round 13도 여전히 Mock/dry-run 기반이다(코드는 실제 호출 준비가
됐지만 Credential이 없어 자연히 dry-run으로 남는다). Round 13이 새로 확인한 한계:
- **DART/Naver News는 Credential이 있어도 아직 동작하지 않는다** — 어댑터 코드
  자체가 stub이다(회사명→corp_code 매핑 등 추가 설계 필요, `docs/
  RC2_CONNECTION_CHECKLIST.md` §1 참고).
- **n8n 실제 배포 코드는 실제 n8n 인스턴스로 검증되지 않았다** — Public API
  문서 기준으로 작성했으나, `tags` 필드 등 세부 계약은 실제 Credential이 준비되면
  1회 실행으로 재확인이 필요하다.

Round 12가 확인한 한계(계속 유효):
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
