# Pilot Demo Package — LCIP Pilot 실제 시연용 패키지

Architect Review Round 11 Priority 4("실제 시연용 패키지를 만든다")에 따라 작성한
문서다. 새로운 리서치·기능을 추가하지 않고, Round 8~10이 이미 완성한 5개 Scenario와
Round 10 Data Sprint가 채운 TOP10 Knowledge, Round 11이 완성한 Home Dashboard/
Executive Report를 조합해 "지금 그대로" 시연 가능한 흐름만 정리한다.

전제: 이 Pilot은 RC1(ADR-010) 기준 — **외부 API 실제 호출 없음**(Feature Flag 전부
`false`), Financial Provider는 Mock, 뉴스/정책 분석은 fixture 기반이다. 시연 시작
전에 반드시 이 사실을 청중에게 알린다("Mock/dry-run 결과가 섞여 있다").

---

## 1. Demo Dataset

Round 10 Data Sprint가 실제 Knowledge를 채운 TOP10 중, 발표 순서(§5)에 실제로
등장하는 3개사를 Demo Dataset으로 고정한다.

| 순번 | 회사 | 선정 이유 |
|---|---|---|
| 1 | **LX Hausys** | LX홀딩스 계열사 본인 — TOP-0001(실리코시스) 리스크의 당사자 관점 |
| 2 | **KCC** | LX Hausys의 실제 Comparable Peer(Round 10에서 Architect가 직접 지정) — 국내 경쟁사 비교 시연 |
| 3 | **Caesarstone** | 실제 배심원 평결·법원 판결까지 확인된 실리코시스 소송 노출 사례 — 리스크 관리 미션과 가장 직접적으로 연결되는 회사 |

Topic은 `TOP-0001`(엔지니어드스톤·실리코시스) 하나로 고정한다 — 여러 Topic을
섞으면 "무엇을 보여주는 Pilot인지" 흐려진다는 점을 Round 9부터 계속 경계해 왔다.

---

## 2. Demo Scenario (실행 순서 및 명령)

Round 10이 검증한 발표 순서를 그대로 따르되, Round 11이 완성한 Home Dashboard를
0번(첫 화면)으로 앞에 추가한다.

| 순번 | 내용 | 명령 |
|---|---|---|
| 0 | Home Dashboard — 첫 화면 | Scenario 1(§5행)이 실행될 때마다 `output/pilot_data/dashboard.html`이 갱신된다 — 처음 열 때 비어 있으면 Step 5(뉴스 분석)를 먼저 1회 실행한 뒤 새로고침한다 |
| 1 | LX Hausys Quick Company Scan + Investment Review | `python3 scripts/scenarios/scenario_3_investment_review.py "LX Hausys"` |
| 2 | KCC Quick Company Scan + Investment Review (Peer 비교) | `python3 scripts/scenarios/scenario_3_investment_review.py "KCC"` |
| 3 | Caesarstone Quick Company Scan + Investment Review (실제 소송 사례) | `python3 scripts/scenarios/scenario_3_investment_review.py "Caesarstone"` |
| 4 | 정부 정책 영향 분석 | `python3 scripts/scenarios/scenario_4_policy_impact.py` |
| 5 | 뉴스 분석 + Email Preview | `python3 scripts/scenarios/scenario_1_news_analysis.py` |

Scenario 3은 내부적으로 Scenario 2(Quick Company Scan)를 호출하므로 명령 1개로
"입력 → Quick Scan → Investment Review → Export(JSON/Markdown/Executive Report
HTML)"까지 전부 끝난다(Round 11 Priority 2로 클릭 수를 줄인 부분).

---

## 3. 시연 순서 (단계별 대본)

### 준비 (시연 시작 전)

1. 터미널 창 1개, 브라우저 창 1개를 미리 열어 둔다.
2. `output/` 폴더를 비워 시작한다(이전 시연 잔여 파일과 섞이지 않도록) —
   `rm -rf output/pilot_data output/quick_company_scan_exports`.
3. 청중에게 "이 Pilot은 실제 API를 호출하지 않고, 이미 리서치한 공개정보와 Mock
   응답으로 동작합니다"를 먼저 알린다.

### Step 0 — Home Dashboard (약 30초)

- 브라우저에서 `output/pilot_data/dashboard.html`을 연다. 시연 중 아직 파일이 없으면
  Step 5(뉴스 분석)를 먼저 1회 실행해 생성한 뒤 다시 연다.
- "이게 전략팀 직원이 매일 아침 보게 될 첫 화면입니다"라고 설명하며 5개 카드를
  순서대로 짚는다: 오늘의 핵심 Intelligence → Quick Company Scan 실행 방법 →
  Investment Review 실행 방법 → 최근 분석 결과 → 최근 뉴스.
- "실행 버튼이 클릭형이 아니라 명령어로 되어 있는 이유"를 정직하게 설명한다 —
  Pilot은 서버 없이 정적 HTML + CLI 스크립트로 동작하는 구조이기 때문이다(§4
  예상 질문 Q1 참고).

### Step 1~3 — 3개사 Quick Company Scan (각 약 1분)

각 회사마다 다음을 반복한다(LX Hausys → KCC → Caesarstone 순서):

1. 터미널에서 `python3 scripts/scenarios/scenario_3_investment_review.py "회사명"`을
   실행한다.
2. 실행이 끝나면 터미널 맨 아래 "결과 요약" 블록(Round 11 Priority 2로 추가됨)을
   그대로 읽는다 — 회사명, Company Intelligence Score, 추천 신호, 추천 사유,
   보고서 3종 경로가 바로 보인다.
3. `{회사명}_executive_report.html`을 브라우저로 열어 "이게 임원에게 그대로 전달할
   수 있는 1페이지 요약본입니다"라고 보여준다(Round 11 Priority 3).
4. Caesarstone 차례에서는 Markdown 상세 보고서(`.md`)를 열어 §10 Risk에 실제
   배심원 평결·법원 판결 근거가 원문 URL과 함께 있는 것을 보여준다 — "이 Pilot이
   임의로 지어낸 내용이 아니다"를 증명하는 대목이다.

### Step 4 — 정부 정책 영향 분석 (약 30초)

- `python3 scripts/scenarios/scenario_4_policy_impact.py` 실행.
- "정부 정책이 발표되면 그 영향을 LX 계열사 관점에서 분석하는 기능입니다"라고
  설명하되, "지금은 예시 입력 기반 Mock 결과입니다"를 반드시 함께 말한다.

### Step 5 — 뉴스 분석 + Email Preview (약 30초)

- `python3 scripts/scenarios/scenario_1_news_analysis.py` 실행.
- 마지막에 출력되는 Email Preview(dry-run, 실제 발송 없음)를 보여주며 "매일 아침
  이런 형태로 이메일이 갈 수 있다"고 설명한다.
- 마지막으로 Home Dashboard를 새로고침해 "최근 분석 결과"와 "최근 뉴스" 카드에
  방금 실행한 내용이 반영된 것을 보여주며 마무리한다.

전체 소요 시간: 약 4~5분.

---

## 4. 예상 질문과 답변 (FAQ)

**Q1. Home Dashboard의 "실행" 버튼을 왜 클릭할 수 없나요?**
Pilot은 별도 백엔드 서버가 없는 정적 HTML + CLI 구조입니다(RC1 정의, ADR-010).
클릭형 버튼을 만들려면 서버가 필요한데, 이번 Sprint는 "새 Engine/Framework
금지"가 절대 제약이라 실제로 동작하지 않는 버튼을 만드는 대신, 정확한 명령어를
그대로 보여주는 방식을 선택했습니다.

**Q2. 방금 본 결과 중 어디까지가 진짜(실제 리서치)이고 어디까지가 Mock인가요?**
Company Overview/Business Structure/Competitor/일부 Risk 항목은 Round 10에서
WebSearch로 실제 확인한 내용(원문 URL 포함)입니다. Financial Snapshot의 배수,
LX Strategic Fit, 뉴스/정책 분석은 아직 Mock입니다. Confidence가 "low"로 표시된
항목은 전부 초안 참고용입니다 — Markdown 상세 보고서의 "확인되지 않은 사항" 절에
정직하게 나열되어 있습니다.

**Q3. 왜 30개사 전부가 아니라 3개사만 보여주나요?**
Round 10 Data Sprint에서 TOP10(핵심 비교군)만 실제 Knowledge를 채웠고, 이번 Round
11은 데이터 확장이 아니라 "이미 있는 데이터로 사용성을 검증"하는 Sprint이기
때문입니다(절대 제약: 새 회사 리서치 금지). 나머지 20개사는 지금 실행하면 여전히
"mock: ... 미확인"만 나옵니다.

**Q4. 이 결과를 그대로 투자 의사결정에 써도 되나요?**
아니오. Investment Review는 "최종 투자판단"이 아니라 "심층 검토가 필요한지"를
가리는 스크리닝 신호까지만 제공합니다(`knowledge/INVESTMENT_FRAMEWORK.md`). DCF/
LBO/Option 가치평가는 Enterprise Backlog로 의도적으로 미구현 상태입니다.

**Q5. Executive Report(HTML)와 기존 Markdown 보고서는 뭐가 다른가요?**
Markdown은 Core 7개 필드 전체와 Peer 비교표까지 담은 상세본이고, Executive
Report(HTML)는 임원이 3분 안에 볼 수 있도록 점수·추천신호·근거·Top 3 미확인
사항만 추린 1페이지 요약본입니다(Round 11 Priority 3). Pilot은 PDF를 지원하지
않습니다 — 필요하면 브라우저의 "인쇄 → PDF로 저장" 기능을 쓰면 된다.

**Q6. 다음 단계(RC2)는 무엇인가요?**
실제 Anthropic API/DART/SEC 등 외부 API 연결입니다. Feature Flag는 이미 준비돼
있고(`config/feature_flags.yaml`), Credential Checklist도 `docs/
CONNECTION_READINESS.md`에 정리돼 있습니다. Architect 승인이 있어야 시작합니다.

---

## 5. Demo Script (발표자용 대본 요약)

> "지금부터 LCIP Pilot을 보여드리겠습니다. 이 Pilot은 LX홀딩스 전략팀이 공개정보만
> 사용해서 산업 리스크와 기회를 모니터링하는 개인용 도구입니다. 먼저 전략팀
> 직원이 매일 아침 열어볼 첫 화면부터 보여드리겠습니다."
> *(Home Dashboard 시연, §3 Step 0)*
>
> "이제 실제로 회사 하나를 조사해 보겠습니다. LX Hausys부터 시작해서, 실제
> Comparable Peer인 KCC, 그리고 실제 소송 이력이 있는 Caesarstone까지
> 순서대로 보여드리겠습니다. 명령 하나로 회사 개요부터 투자 시그널까지 전부
> 나옵니다."
> *(Step 1~3 시연)*
>
> "회사 조사 외에도 정부 정책 영향 분석과 매일 뉴스 분석 기능이 있습니다."
> *(Step 4~5 시연)*
>
> "정리하면, 이 Pilot은 아직 외부 API에 연결되지 않은 상태(RC1)이지만, 구조와
> 실제 데이터 3개사분은 이미 완성되어 있어 지금 이 흐름 그대로 실제 API만
> 연결하면 바로 운영 가능한 수준입니다."

---

## 참고

이 문서는 새 기능이 아니라 기존 Scenario 5종·Home Dashboard·Executive Report의
**사용 순서**만 정리한 것이다 — 코드 변경 없음. 새 회사·리서치가 필요해지면
`config/technical_debt_registry.yaml`의 TD-005(나머지 20개사 Knowledge 미보유)를
참고해 다음 Data Sprint에서 검토한다.
