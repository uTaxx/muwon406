---
information_class: public
document_type: knowledge
company: LX Holdings
source_types: [news, trade_press, exchange_data]
reference_date: 2026-08-05
last_reviewed: 2026-08-05
source_urls:
  - https://stockanalysis.com/quote/krx/383800/company/
  - https://www.koreatimes.co.kr/business/companies/20250510/lx-group-cruises-toward-stable-growth-in-5th-year-of-independence
confidence: medium
version: 0.4
owner: user (Architect Review Round 6 — TASK-K01)
knowledge_taxonomy_version: 1.0
---

# LX Holdings Context

> TASK-004A(Knowledge Foundation Builder) 산출물. `knowledge/KNOWLEDGE_POLICY.md`의
> 16계층 Taxonomy를 **전부** 사용한다 (Architect Review Round 3 Q5) — 모든 Knowledge
> 문서는 동일한 템플릿을 가져야 하므로, 지주회사에 해당하지 않는 계층(Product/
> Manufacturing/Value Chain/Customer/Competitor/Raw Material)도 삭제하지 않고 **N/A**로
> 표기해 구조를 유지한다. `knowledge/KNOWLEDGE_POLICY.md` §4 우선순위 6위 문서.
>
> 본 문서는 공개정보로 확인된 사실만 기록한다. 아직 출처가 확인되지 않은 항목은 모두
> `TODO: source required`로 남겨두었으며, 임의로 채우지 않는다.

## 1. Company — 지주회사 개요·지배구조

- 설립 배경: 2021년 5월 LG그룹에서 분할·독립해 LX홀딩스(LX Holdings Corp.)로 출범한
  투자 지주회사다. (참고: 일부 데이터 벤더는 법인 연혁을 1947년으로 소급 표기하는데,
  이는 LG그룹 창립 연혁을 이어받은 것으로 보이며 LX홀딩스 자체의 법적 설립일(2021년
  5월)과는 다른 개념이다 — 혼동하지 않도록 별도 명시한다.)
- 본사 소재지: 서울(구체적 주소는 TODO: source required)
- 상장 여부·거래소: 코스피 상장, KRX 티커 383800
- 대표이사·이사회 구성: TODO: source required
- 지분 구조: TODO: source required (DART 대량보유 보고서 참고)
- Source: stockanalysis.com, Korea Times, EconoTimes
- Reference URL: https://stockanalysis.com/quote/krx/383800/company/ ,
  https://www.koreatimes.co.kr/business/companies/20250510/lx-group-cruises-toward-stable-growth-in-5th-year-of-independence ,
  https://www.econotimes.com/LG-Group-launches-LX-Holdings-1607710
- Confidence: medium
- Last Verified: 2026-08-05

## 2. Business — 주요 계열사 (Portfolio)

2025년 5월 기준 보도(Korea Times)에 따르면 LX그룹은 LG그룹에서 분리 당시 11개였던
계열사가 17개로 늘었다. 확인된 주요 계열사와 지분율은 다음과 같다:

| 계열사 | 상장 여부 | LX홀딩스 지분율 | 주요 사업 |
|---|---|---|---|
| LX International(KRX: 001120) | 상장 | 26.8% | 트레이딩·자원개발·물류투자 |
| LX Hausys(KRX: 108670) | 상장 | 33.5% | 건축자재·자동차소재 |
| LX Semicon(KRX: 108320) | 상장 | 33.1% | 반도체(디스플레이 구동칩 등) |
| LX MMA | 비상장 | 50.0% | 화학(MMA) |
| LX MDI | 비상장 | 100.0% | TODO: source required |
| LX Ventures | 비상장 | 100.0% | 벤처투자 |
| LX Pantos | 비상장(LX International 자회사) | LX International 지분 75.9% | 종합물류 |
| LX Glas(舊 한글라스 인수) | 비상장(LX International 자회사) | LX International 지분 100.0% | 유리 |
| Poseung Green Power | 비상장(LX International 자회사) | LX International 지분 70.0% | 발전 |

계열사별 매출 비중(그룹 연결 기준)은 확인하지 못했다.

- Source: Korea Times, stockanalysis.com(LX International/LX Semicon/LX Hausys 개별 페이지)
- Reference URL: https://www.koreatimes.co.kr/business/companies/20250510/lx-group-cruises-toward-stable-growth-in-5th-year-of-independence ,
  https://stockanalysis.com/quote/krx/001120/company/ , https://stockanalysis.com/quote/krx/108320/
- Confidence: medium
- Last Verified: 2026-08-05

## 3. Product — N/A

지주회사는 자체 제품을 생산·판매하지 않는다. 개별 제품 정보는 각 계열사 문서
(`LX_HAUSYS_COMPANY_DNA.md` 등)를 참고한다.

- 내용: Not Applicable (지주회사)
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 4. Manufacturing — N/A

지주회사는 생산 시설을 직접 운영하지 않는다. 생산 거점 정보는 각 계열사 문서를 참고한다.

- 내용: Not Applicable (지주회사)
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 5. Value Chain — N/A (그룹 지배구조 관점으로 대체)

지주회사 자체의 원재료→생산→판매 Value Chain은 없다. 대신 "계열사 포트폴리오를 통한 그룹
차원의 사업 배치"가 지주회사 관점의 상응 개념이다 — 상세는 §2 Business와 각 계열사 Value
Chain 문서(`LX_HAUSYS_VALUE_CHAIN.md` 등)를 참고.

- 내용: Not Applicable (지주회사 자체 Value Chain 없음) — §2 참고
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 6. Customer — N/A

지주회사는 최종 고객에게 직접 판매하지 않는다. 고객 정보는 각 계열사 문서를 참고한다.

- 내용: Not Applicable (지주회사)
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 7. Competitor — N/A (그룹 단위 비교로 대체 가능)

지주회사는 사업적으로 직접 경쟁하는 대상이 없다. 지주회사 형태(순수 지주회사/사업 지주회사
등) 비교가 필요하면 이 섹션에 향후 기록한다.

- 내용: Not Applicable (지주회사) — 향후 확장 시 국내 타 지주회사와의 비교 검토
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 8. Raw Material — N/A

지주회사는 원재료를 직접 조달하지 않는다. 원재료 정보는 각 계열사 문서를 참고한다.

- 내용: Not Applicable (지주회사)
- Source: N/A / Reference URL: N/A / Confidence: N/A / Last Verified: N/A

## 9. Government — 관련 규제·공시 체계

코스피 상장사로서 금융감독원 전자공시(DART)·한국거래소 공시 규정을 따른다. 지주회사
특유의 추가 규제(공정거래법상 지주회사 행위제한 등)는 이번 라운드에서 확인하지 못했다.

- 내용: 코스피 상장사 공시 의무(DART/한국거래소) — 지주회사 특유 규제는 TODO: source required
- Source: stockanalysis.com(상장 정보)
- Reference URL: https://stockanalysis.com/quote/krx/383800/company/
- Confidence: medium
- Last Verified: 2026-08-05

## 10. Risk — 재무·리스크 개요

stockanalysis.com 집계 기준(2024년), LX홀딩스 매출은 194.51(단위 표기 불명확 — 원 자료가
"billion"으로 번역 표기했으나 실제로는 억원 단위일 가능성이 있어 그대로 인용하되 단위를
확정하지 않는다)로 전년 대비 64.67% 증가, 이익은 157.26으로 전년 대비 99.46% 증가했다고
집계된다 — **단위 및 정확한 수치는 DART 사업보고서 원문 대조 전까지 확정하지 않는다**
(TODO: source required). 사업보고서 "위험요소" 항목과 지속가능경영보고서 기준 ESG/리스크
관리 방향은 아직 확인하지 못했다.

- 내용: 2024년 매출·이익 증가 추세(단위 미확정, 자료: stockanalysis.com) — 정확한
  금액/단위는 DART 원문 대조 필요
- Source: stockanalysis.com
- Reference URL: https://stockanalysis.com/quote/krx/383800/company/
- Confidence: draft (수치 단위 미확정이므로 medium이 아닌 draft로 낮춰 표기)
- Last Verified: 2026-08-05

## 11. Opportunity — 전략 방향

Korea Times 보도(2025년 5월)에 따르면 LX그룹은 적극적 확장 전략을 추진 중이며, 유리
제조사(한글라스, 現 LX Glas)를 인수했고 바이오매스·물류 분야 기업에도 투자해 포트폴리오를
다각화하고 있다. 계열사 수는 분리 당시 11개에서 17개로 늘었다(2025년 4월 기준 보도).

- 성장 Driver: M&A를 통한 포트폴리오 다각화(유리·바이오매스·물류), 계열사 수 11→17개 확대
- Source: Korea Times
- Reference URL: https://www.koreatimes.co.kr/business/companies/20250510/lx-group-cruises-toward-stable-growth-in-5th-year-of-independence
- Confidence: medium
- Last Verified: 2026-08-05

## 12. Investment Point — LX Hausys와의 관계

LX홀딩스는 LX Hausys 지분 33.5%를 보유한 최대주주다(2번 항목 표 참고). LX Hausys는
그룹 내 건축자재·자동차소재 사업을 담당하는 상장 계열사로, TOP-0001(엔지니어드스톤·
실리코시스) 리스크 분석 시 지주회사 관점에서는 "계열사 지분가치·평판 리스크 전이" 경로로
연결된다.

- 지분율 및 지배구조상 위치: LX홀딩스가 33.5% 보유(최대주주), LX Hausys는 코스피 상장
  계열사(KRX: 108670)
- 그룹 내 사업적 역할: 건축자재·자동차소재 사업 담당
- Source: Korea Times, stockanalysis.com
- Reference URL: https://www.koreatimes.co.kr/business/companies/20250510/lx-group-cruises-toward-stable-growth-in-5th-year-of-independence ,
  https://stockanalysis.com/quote/krx/108670/company/
- Confidence: medium
- Last Verified: 2026-08-05

## 13~16. 문서 전체 출처 요약

- Source: Korea Times / EconoTimes / stockanalysis.com (Round 6 TASK-K01 리서치, DART
  사업보고서·지속가능경영보고서 원문 대조는 다음 라운드 과제)
- Reference URL: 위 각 섹션 참고
- Confidence: medium(전체 문서, 항목별 개별 Confidence는 위 각 섹션 참고 — 재무 수치는
  단위 미확정으로 draft)
- Last Verified: 2026-08-05

---

## 작성 지침 메모 (Claude Code용)

이 섹션 헤더 구조는 Claude API가 부분 로드할 수 있도록 설계되었다. 각 TODO 항목을 채울 때는
반드시 `knowledge/KNOWLEDGE_POLICY.md` §3 서식과 `knowledge/SOURCE_PRIORITY.md` 출처
우선순위를 따른다:

1. 공개 출처(공식 홈페이지 → 사업보고서 → 지속가능경영보고서 → DART → IR 자료 → 공식
   보도자료 → 정부자료 → 언론 → RSS 순)의 URL을 항목별 `Reference URL`과 문서 상단
   `source_urls`에 추가
2. 문서 상단 `reference_date`(공시 기준일)와 `last_reviewed`, 항목별 `Last Verified`를 갱신
3. `confidence`를 `draft` → `high`로 변경 (출처 확인 후에만)
4. **N/A로 표기된 계층(3,4,5,6,7,8)은 삭제하지 않는다** — Architect Review Round 3 Q5
   원칙: 모든 Knowledge 문서(회사 프로필류)는 동일한 16계층 템플릿을 유지해야 하므로,
   해당 없는 계층도 구조상 자리를 유지한 채 N/A로 남긴다.
