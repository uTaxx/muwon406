---
information_class: public
document_type: framework
company:
source_types: []
reference_date:
last_reviewed: 2026-08-05
source_urls: []
confidence: high
version: 1.0
owner: Architect Review (2026-08-05)
---

# Quick Company Scan Framework

> TASK-004D 산출물. **LCIP의 핵심 엔진**이다 — 단순 기업조사가 아니라, 향후 Investment
> Review Engine(Enterprise 단계)의 **입력(Input)**이 된다. 출력 구조는
> `schemas/quick_company_scan.schema.json`으로 검증하며, 실제 사용은
> `prompts/quick_scan.md`가 담당한다 (Pilot에서는 아직 파이프라인에 연결되지 않음, Sprint 6
> 확장 대상).

## 0. 절대 원칙 (기존 quick_scan.md 원칙과 동일, 확장판에도 그대로 적용)

1. **사용자가 명시적으로 지정한 기업만** 스캔한다. 임의로 대상을 추가하지 않는다.
2. 공개정보(`SOURCE_PRIORITY.md` 우선순위)만 사용한다.
3. 사실·해석·추론·제안을 구분한다.
4. **최종 투자 판단을 내리지 않는다** — "검토 대상으로서의 스크리닝 신호"까지만 제공한다.
   `investment_recommendation`은 매수/매도 조언이 아니라 "추가 검토 진행 여부"에 대한
   신호일 뿐이다.
5. 확인되지 않은 재무 수치·비공개 협상 정보·밸류에이션을 추정하지 않는다 —
   `estimated_valuation`은 공개된 배수(comparable multiple)가 실제로 존재할 때만 채우고,
   없으면 명시적으로 `null` + 사유를 남긴다.

## 1. 20개 항목 정의

| # | 항목 | 설명 | Taxonomy 연결 |
|---|---|---|---|
| 1 | Company Overview | 법인 개요, 연혁, 소재지 | Knowledge Taxonomy #1 Company |
| 2 | Business Structure | 사업부/자회사 구성 | Taxonomy #2 Business |
| 3 | Product Portfolio | 주요 제품/브랜드 | Taxonomy #3 Product |
| 4 | Manufacturing | 생산 거점/공정 | Taxonomy #4 Manufacturing |
| 5 | Value Chain | 원재료~고객 흐름 | Taxonomy #5 Value Chain |
| 6 | Customer | 고객 산업/구조 | Taxonomy #6 Customer |
| 7 | Competitor | 경쟁사/시장 지위 | Taxonomy #7 Competitor |
| 8 | Financial Snapshot | 공개된 매출/영업이익/부채 등 스냅샷 | 신규 (재무) |
| 9 | Capital Market | 상장 여부, 시가총액, 최근 자본시장 활동 | Taxonomy #11 Opportunity와 연결 |
| 10 | Investment Multiple | 공개된 배수(P/E, EV/EBITDA 등) — 확인 안 되면 null | 신규 (재무) |
| 11 | Comparable Companies | 비교 가능한 동종 상장/비상장 기업 | 신규 |
| 12 | Growth Strategy | 공식 발표된 성장 전략 | Taxonomy #11 Opportunity |
| 13 | Government Exposure | 관련 정부/규제 노출 | Taxonomy #9 Government |
| 14 | Risk Assessment | 공개된 리스크 요인 | Taxonomy #10 Risk / `MISSION_FRAMEWORK.md` risk_management |
| 15 | Opportunity Assessment | 공개된 성장기회 | Taxonomy #11 Opportunity / `MISSION_FRAMEWORK.md` future_readiness |
| 16 | LX Strategic Fit | LX홀딩스/계열사 사업과의 연관성·시너지 여지 | Taxonomy #12 Investment Point |
| 17 | Investment Recommendation | 스크리닝 신호(아래 §2) — 투자 조언 아님 | 신규 |
| 18 | Estimated Valuation | 공개 배수 기반 추정치, 없으면 null | 신규 |
| 19 | Synergy Analysis | LX 기존 사업과의 시너지 가능 영역 | `INVESTMENT_FRAMEWORK.md` §2와 연동 |
| 20 | Reference Sources | 전체 근거 URL 목록 (필수, 최소 1개) | Taxonomy #13~14 |

## 2. Investment Recommendation — 스크리닝 신호 정의

`investment_recommendation.signal`은 아래 4개 값 중 하나이며, **투자 여부의 최종 결론이
아니라 "다음 단계로 무엇을 할지"에 대한 절차적 신호**다.

| 값 | 의미 |
|---|---|
| `proceed_to_deep_review` | 공개정보만으로도 LX 관점 연관성이 확인되어 정식 DD 검토를 제안 |
| `monitor` | 현재는 근거 부족하지만 지속 모니터링 가치가 있음 |
| `insufficient_public_information` | 공개정보가 부족해 스크리닝 자체가 불가능 |
| `not_aligned_based_on_available_facts` | 확인된 공개 사실 기준으로 LX 사업과의 연관성이 낮음 |

`rationale` 필드에 이 신호를 선택한 근거(확인된 사실 기반)를 반드시 명시한다.

## 3. Estimated Valuation — 임의 추정 금지 규칙

- 공개된 비교기업 배수(P/E, EV/EBITDA, PSR 등)가 실제로 확인될 때만 `estimated_valuation`을
  채운다. 이때도 "추정 범위"이지 확정값이 아님을 명시한다.
- 대상 기업의 비공개 재무제표를 유추해서 밸류에이션을 만들지 않는다.
- 확인 불가 시 `estimated_valuation: null`이며 `unknowns`에 "공개 배수 정보 없음"을 기록한다.

## 4. Quick Company Scan → Investment Review Engine 관계

Pilot 단계의 Quick Company Scan은 완결된 투자 의사결정 도구가 아니라, **향후 Enterprise
단계 Investment Review Engine의 표준 입력 포맷**이다. 즉 이 20개 항목은:

- 사람(전략팀)이 1차 스크리닝 자료로 바로 활용 가능해야 하고,
- 동시에 향후 자동화된 Investment Review Engine이 파싱할 수 있는 구조화된 JSON
  (`schemas/quick_company_scan.schema.json`)이어야 한다.

## 5. 출력 형식

`schemas/quick_company_scan.schema.json`을 그대로 준수한다. 각 섹션은 `knowledge/
KNOWLEDGE_POLICY.md` §3과 동일하게 근거(evidence)를 가져야 하며, 전체 스캔은 최상위
`reference_sources`에 모든 근거 URL을 모은다.
