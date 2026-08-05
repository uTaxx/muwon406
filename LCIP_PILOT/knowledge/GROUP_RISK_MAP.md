---
information_class: public
document_type: knowledge
company: LX Holdings / LX Hausys
source_types: [news, trade_press, legal_press]
reference_date: 2026-08-05
last_reviewed: 2026-08-05
source_urls:
  - https://news.bloomberglaw.com/insurance/artificial-stone-silica-suits-set-up-insurance-coverage-fights
  - https://www.aboutlawsuits.com/silicosis-lawsuit/
  - https://www.dailyjournal.com/articles/380327-engineered-stone-companies-found-partially-liable-for-worker-s-silicosis
confidence: medium
version: 0.3
owner: user (Architect Review Round 6 — TASK-K01)
knowledge_taxonomy_version: 1.0
---

# Group Risk Map

> 리스크 관리 미션(`knowledge/MISSION_FRAMEWORK.md`)의 핵심 참조 문서, 16계층 Taxonomy
> (`knowledge/KNOWLEDGE_POLICY.md`)의 "10. Risk" 항목을 그룹 단위로 집계한 것이다.
> `knowledge/KNOWLEDGE_POLICY.md` §4 우선순위 3위 문서. 계열사별로 확인된 공개 리스크
> 요인만 기록하며, 확인되지 않은 리스크는 추정하지 않는다.

## 1. 리스크 카테고리 정의 (MISSION_FRAMEWORK.md risk_management 서브카테고리와 동일)

- 소송·제품책임 (`litigation` / `product_liability`)
- 산업안전 (`safety`)
- 환경 (`environmental`)
- 통상 (`regulatory`)
- 환율 (`fx`)
- 원자재 (`raw_material`)
- 공급망 (`supply_chain`)
- 정책·규제 (`policy` / `regulatory`)
- ESG (`esg`)

## 2. LX Hausys — 엔지니어드스톤·실리코시스 (TOP-0001)

- 카테고리: `litigation`, `safety`, `regulatory`
- **확인된 공개 리스크 사실(Round 6 TASK-K01 리서치, 2026-08-05 기준)**:
  - LX Hausys Ltd.의 미국 법인이 Cambria Enterprises LLC 등 다른 엔지니어드스톤
    제조·유통업체와 함께, 실리카 관련 소송에 대한 보험 커버리지 분쟁(실리카 면책조항
    적용 여부)에서 이름이 언급됐다 (Bloomberg Law, 2026). **주의**: 이는 "보험 커버리지
    분쟁에 이름이 언급됨"이라는 확인된 사실이며, 특정 개별 소송(아래 업계 사례)의
    피고로 확정됐다는 의미는 아니다 — 개별 사건 피고 여부는 법원 공개기록 대조가
    추가로 필요하다(TODO: source required).
  - 업계 전반 맥락(LX Hausys가 피고로 명시되지는 않았으나 시장 상황 이해에 참고):
    2024년 8월 로스앤젤레스 배심원이 엔지니어드스톤 제조사들에 실리코시스 관련 $52M
    평결을 내렸고, 2026년 5월 콜로라도 배심원은 인조석 가공 노동자 Tyler Jordan에게
    $17.45M을 평결했다(각각 aboutlawsuits.com, Daily Journal 보도).
  - 자사 제품(VIATERA)의 결정형 실리카(쿼츠) 함량은 자사 공식 발표 기준 최대 93%다
    (`LX_HAUSYS_COMPANY_DNA.md` §8 참고) — 업계 전반의 실리코시스 소송 핵심 쟁점과
    동일한 성분이 자사 제품에도 존재함을 의미한다(자사 발표 사실 자체이며, 소송
    결과에 대한 예단은 아니다).
- 관련 규제·사법기관: 미국 OSHA(산업안전), 캘리포니아·콜로라도 등 각급 주법원
- 관련 지역: 미국, 호주, 캐나다, 영국, EU (`config/topics.yaml` TOP-0001 기준)
- Source: Bloomberg Law, aboutlawsuits.com, Daily Journal
- Reference URL: https://news.bloomberglaw.com/insurance/artificial-stone-silica-suits-set-up-insurance-coverage-fights ,
  https://www.aboutlawsuits.com/silicosis-lawsuit/ ,
  https://www.dailyjournal.com/articles/380327-engineered-stone-companies-found-partially-liable-for-worker-s-silicosis
- Confidence: medium (업계 법률매체 보도 기준, 법원 공개기록 원문 미대조)
- Last Verified: 2026-08-05

## 3. 기타 계열사 리스크 (Pilot 범위 밖 — 향후 확장)

> Pilot은 TOP-0001(엔지니어드스톤·실리코시스)만 다룬다. 다른 계열사·리스크 카테고리는
> Enterprise 전환 이후 확장 대상이며, 이 문서에서는 자리만 확보해둔다.

- TODO: 향후 Topic 추가 시 이 섹션에 카테고리·계열사·근거 링크를 추가

## 4. 갱신 규칙

이 문서는 사람이 수기로 채우는 정적 문서가 아니라, Master Pipeline의 AI Analyze 단계(舊
WF-P05) 심층분석 결과 중 `significance`가 높은 건이 누적되면 주기적으로 요약을 반영하는
문서다 (자동 갱신은 Pilot 범위 밖이며, TASK-012 Dashboard가 이 역할의 상당 부분을 대체한다).
이 파일은 Claude Context에 로드되는 "확정된 배경지식" 용도로 유지한다.
