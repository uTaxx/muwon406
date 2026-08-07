# Project Status

최종 갱신: 2026-08-07 (Architect Review Round 11 반영)

## 요약

TASK-001~007 → Round 2~10(Knowledge/Provider/Registry/Coverage/Scenario화/RC1 정의/
Data Sprint) → **Round 11("Pilot RC1 User Validation" UX Sprint) 반영** 완료.
Architect는 "전체 검토 결과를 승인한다. Round 10을 기점으로 Data Sprint도
종료한다. Pilot은 이제 '개발 프로젝트'가 아니라 '사용성 검증 프로젝트'로
전환한다"고 선언하며 **새로운 회사 리서치/Registry/Layer/Engine/Framework/
Dashboard Widget/Enterprise 기능을 절대 금지**하고, "실제 전략팀 직원이 사용하는
흐름을 만든다"를 유일한 목표로 지정했다.

이번 Round는 새 구조를 하나도 추가하지 않고 **이미 있는 기능을 연결·다듬었다**:
Home Dashboard(5개 카드로 첫 화면 완성), Quick Company Scan 실행 후 터미널에
바로 뜨는 "결과 요약"(파일을 열지 않아도 핵심이 보임), Executive Report(HTML,
임원 보고용 1페이지 자동 생성), Pilot Demo Package(실제 시연 대본), User Guide
(전략팀 관점 재작성) 5가지를 완성했다.

## Round 11 Priority 5개 처리 결과

| 순위 | 항목 | 상태 | 핵심 내용 |
|---|---|---|---|
| 1 | Home Dashboard | ✅ 완료 | `dashboard/template.html`에 새 `<section id="home">` 추가 — 5개 카드(오늘의 핵심 Intelligence/Quick Company Scan 실행/Investment Review 실행/최근 분석 결과/최근 뉴스). 새 Widget 클래스 없이 기존 6개 Widget 데이터의 상위 1건만 재사용(`HOME_*` 토큰 4개, `build_dashboard.py`). 이전까지 미사용이던 `articles` 인자를 `recent_news` 키로 처음 활용(`dashboard_feed.py`) |
| 2 | Quick Company Scan UX 개선 | ✅ 완료 | `scenario_3_investment_review.py` `main()` 실행 마지막에 "결과 요약"(회사명/점수/추천신호/근거/파일 경로 3종) 블록을 터미널에 바로 출력 — Export 파일을 열지 않아도 핵심 확인 가능 |
| 3 | Executive Report 자동 생성 | ✅ 완료 | `quick_company_scan.py`에 `build_executive_report_html()`/Export 단계 확장 — 점수·투자시그널·근거·Top3 미확인사항만 담은 1페이지 HTML을 `{회사명}_executive_report.html`로 자동 생성(HTML만 지원, PDF 미구현) |
| 4 | Pilot Demo Package | ✅ 완료 | `docs/PILOT_DEMO_PACKAGE.md` 신설 — Demo Dataset(LX Hausys/KCC/Caesarstone), Demo Scenario(명령어 표), 시연 순서(단계별 대본), 예상 질문 6개, Demo Script |
| 5 | User Guide 재작성 | ✅ 완료 | `docs/USER_GUIDE.md` 신설 — 개발자 관점(README.md)과 분리, 전략팀 직원이 5분 안에 "회사 조사 → 결과 보기 → Dashboard 보기"를 끝낼 수 있도록 재작성 |

## 테스트 결과

```text
$ pytest tests/ -q                                    -> 전부 PASS (409개 테스트, Round 10: 402개 → +7개)
$ python scripts/scenarios/scenario_3_investment_review.py "LX Hausys"    -> PASS (결과 요약 + Executive Report HTML 생성 확인)
$ python scripts/scenarios/scenario_1_news_analysis.py                    -> PASS (Home Dashboard "최근 뉴스" 반영 확인, {{ 토큰 누락 없음)
$ python scripts/build_dashboard.py --data dashboard/sample_data.json     -> PASS (Home 5개 카드 렌더링 확인)
```

## Round 11에서 새로 생성/수정된 파일

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
- Round 2~10의 각 Q 항목·추가 지시: `CHANGELOG.md`에 라운드별 상세 기록

## 남은 사용자 작업 / 알려진 한계

`TODO.md` 참고 — Round 11도 여전히 Mock/dry-run 기반이며 코드 구조는 동결 상태다
(Architect 지시: "새로운 기능/구조는 구현하지 않는다"). Round 11이 새로 확인한 한계:
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
