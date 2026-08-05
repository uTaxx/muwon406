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

# Corporate Intelligence Taxonomy

> TASK-004E 산출물. LCIP가 다루는 모든 Intelligence(수집된 Article, 분석된 Intelligence
> 레코드)를 분류하는 **표준 분류체계**다. `MISSION_FRAMEWORK.md`(미래준비/리스크관리
> 2축·18개 서브카테고리)가 "이 정보가 왜 중요한가"를 분류한다면, 이 Taxonomy는 "이 정보가
> 어떤 영역(domain)에 속하는가"를 분류한다 — 서로 다른 축이며 함께 사용된다.

## 1. 원칙

**AI는 수집·분석하는 모든 기사를 이 Taxonomy에 매핑해야 한다.** 하나의 기사가 여러
카테고리에 걸칠 수 있으므로 `intelligence_categories`는 배열이다(`mission_category`와 동일
설계 원칙, Architect Review Round 3 Q3/Q4E). 최소 1개 이상 매핑되어야 하며, 매핑이 전혀
안 되면 관련성 자체가 낮다는 신호로 간주한다.

## 2. 19개 카테고리

| 카테고리 (영문) | 값 (enum) | 설명 |
|---|---|---|
| Government | `government` | 정부기관 발표·정책 집행 주체 관련 |
| Policy | `policy` | 정책 방향/입법 변화 |
| Technology | `technology` | 기술 변화, 신소재, 공정 혁신 |
| Investment | `investment` | 투자 유치, 자본 배치 일반 |
| M&A | `ma` | 인수합병, Carve-out, Bolt-on, JV |
| Competitor | `competitor` | 경쟁사 동향 |
| Customer | `customer` | 고객사/전방산업 동향 |
| Supplier | `supplier` | 공급사/원재료 조달처 동향 |
| Raw Material | `raw_material` | 원자재 가격/수급 |
| ESG | `esg` | 환경·사회·지배구조 공개 이슈 |
| Product | `product` | 제품 자체(리콜, 신제품, 품질) |
| Financial | `financial` | 재무 실적, 공시 |
| Capital Market | `capital_market` | 금리, 환율, 증시 등 거시 자본시장 |
| Risk | `risk` | 위 카테고리로 포착되지 않는 일반 리스크 |
| Opportunity | `opportunity` | 위 카테고리로 포착되지 않는 일반 기회 |
| Litigation | `litigation` | 소송, 법적 분쟁 |
| Regulation | `regulation` | 규제 신설/강화/완화 |
| Supply Chain | `supply_chain` | 공급망 재편, 물류, 병목 |
| Macro | `macro` | 거시경제 일반(성장률, 인플레이션 등) |

## 3. Mission Framework와의 관계

이 Taxonomy(도메인 축)와 `MISSION_FRAMEWORK.md`(목적 축)는 독립적으로 함께 매핑된다. 예:

- "미국 캘리포니아 법원, 실리코시스 집단소송 판결" →
  `intelligence_categories: ["litigation", "regulation"]`,
  `mission_category: ["risk_management"]`, `mission_subcategory: ["litigation", "safety"]`
- "경쟁사가 저실리카 신소재 특허 출원" →
  `intelligence_categories: ["technology", "competitor"]`,
  `mission_category: ["future_readiness", "risk_management"]`,
  `mission_subcategory: ["technology"]`

## 4. TOP-0001(엔지니어드스톤·실리코시스)의 주 카테고리

`litigation`, `regulation`, `product`가 핵심이며, 사안에 따라 `government`, `esg`가
추가된다.

## 5. 스키마 반영

`schemas/intelligence.schema.json`, `schemas/claude_output.schema.json`의
`intelligence_categories` 필드가 이 문서의 19개 값을 enum으로 사용한다
(`schemas/google_sheets_columns.json`의 `INTELLIGENCE_DB` 탭에도 동일 컬럼 추가).

## 6. 분류 실패 시 처리

`MISSION_FRAMEWORK.md` §5와 동일 원칙 — 원문만으로 카테고리를 특정할 수 없으면 빈 배열로
두지 않고, 최소한 가장 근접한 카테고리 하나는 남기되 `unknowns`에 불확실성을 기록한다.
카테고리 매핑이 전혀 불가능하면(관련성 자체가 없으면)애초에 Rule Filter 단계에서 제외한다.
