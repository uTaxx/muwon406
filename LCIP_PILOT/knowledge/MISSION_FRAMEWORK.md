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

# Mission Framework

> TASK-004B 산출물. LCIP Pilot의 모든 판단 기준이 되는 최상위 분류 체계다. Master Pipeline의
> Rule Filter/AI Analyze 단계(舊 WF-P04/WF-P05)와 `schemas/intelligence.schema.json` /
> `schemas/claude_output.schema.json`의 `mission_category` / `mission_subcategory` 필드가
> 이 문서를 그대로 따른다. **두 필드 모두 배열(Array)이다** (Architect Review Round 3 Q3) —
> 기사 하나가 미래준비·리스크관리 두 축에 동시에 걸치는 경우가 흔하기 때문이다.

## 1. 원칙

LCIP의 모든 판단(Article, Intelligence)은 반드시 다음 두 축 중 **하나 이상**에 매핑되어야
한다 (`mission_category` 배열에 해당하는 축을 전부 담는다). 어느 축에도 해당하지 않으면
관련성이 낮은 것으로 간주하고 Rule Filter 단계에서 버린다.

## 2. 미래준비 (`future_readiness`)

산업·정책·기술·자본시장 변화 탐지, 성장 기회 발굴이 목적이다.

| mission_subcategory | 의미 |
|---|---|
| `ma` | M&A (인수합병) 신호 |
| `carve_out` | 사업부 분리매각(Carve-out) 신호 |
| `bolt_on` | 기존 사업 보강형 소규모 인수(Bolt-on) 신호 |
| `jv` | 합작법인(Joint Venture) 신호 |
| `venture` | Venture/신규 투자(스타트업 지분투자 등) 신호 |
| `capital_market` | 자본시장 변화(금리, 환율, 원자재 가격 등 투자환경) |
| `technology` | 기술 변화(신소재, 공정혁신, 대체기술 등) |
| `new_business` | 신사업 진출/파일럿 신호 |

## 3. 리스크 관리 (`risk_management`)

소송·안전·환경·통상 등 하방 리스크의 조기 감지가 목적이다.

| mission_subcategory | 의미 |
|---|---|
| `product_liability` | 제품책임(하자, 리콜 등) |
| `environmental` | 환경 규제·오염·배출 관련 |
| `safety` | 산업안전·근로자 보건(예: 실리코시스) |
| `fx` | 환율 변동 리스크 |
| `raw_material` | 원자재 가격/수급 리스크 |
| `supply_chain` | 공급망 중단/재편 리스크 |
| `regulatory` | 규제·입법 변화(세이프가드, 관세 등 포함) |
| `litigation` | 소송(민사/집단소송 등) |
| `policy` | 정부 정책 변화 |
| `esg` | ESG 관련 공개 이슈 |

## 4. TOP-0001(엔지니어드스톤·실리코시스)의 기본 매핑

`config/topics.yaml`의 TOP-0001은 기본적으로 `mission: risk_management`(Topic 레벨 설정,
단일값 — Topic 자체의 주된 목적을 나타내므로 배열이 아니다)이며, 실제 수집되는 개별
Article/Intelligence는 세부적으로 `safety`(산업안전), `litigation`(소송),
`regulatory`(세이프가드·관세 등 규제) 중 하나 이상으로 분류된다. 하나의 Article이 복수
서브카테고리·복수 미션 축에 동시에 걸칠 수 있으므로(예: 소송이면서 동시에 안전 이슈, 또는
규제 강화이면서 동시에 기술전환 기회), `mission_category`와 `mission_subcategory` 둘 다
**처음부터 배열**로 저장한다 — Pilot 단계에서 단일값으로 시작했다가 나중에 배열로 바꾸는
것보다, 지금 배열로 설계하는 편이 훨씬 쉽다는 판단이다.

## 5. 분류 실패 시 처리

원문만으로 `mission_subcategory`를 특정할 수 없으면 빈 배열로 두고 `unknowns`에 그 사실을
남긴다. `mission_category`는 최소 1개 이상 필요하므로(스키마 `minItems: 1`), 관련성 자체가
불확실하면 애초에 Rule Filter/AI Analyze 대상에서 제외한다. 임의로 서브카테고리를 추정하지
않는다 (`PLATFORM_CONSTITUTION.md`의 사실·추론 분리 원칙과 동일).
