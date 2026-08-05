---
information_class: public
document_type: knowledge
company: LX Holdings / LX Hausys
source_types: [DART, sustainability_report, news]
reference_date:
last_reviewed: 2026-08-05
source_urls: []
confidence: draft
version: 0.2
owner: user
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
- 현재 확인된 공개 리스크 사실: TODO: source required (본 문서는 Pilot 최초 구축 시점 기준으로
  비어 있으며, Master Pipeline의 AI Analyze 단계(舊 WF-P05 Risk Analysis, ADR-007로 통합)
  실행 후 INTELLIGENCE_DB의 확정 사실이 누적되면 이 섹션에 요약을 반영한다)
- 관련 지역: 미국, 호주, 캐나다, 영국, EU (`config/topics.yaml` TOP-0001 기준)

## 3. 기타 계열사 리스크 (Pilot 범위 밖 — 향후 확장)

> Pilot은 TOP-0001(엔지니어드스톤·실리코시스)만 다룬다. 다른 계열사·리스크 카테고리는
> Enterprise 전환 이후 확장 대상이며, 이 문서에서는 자리만 확보해둔다.

- TODO: 향후 Topic 추가 시 이 섹션에 카테고리·계열사·근거 링크를 추가

## 4. 갱신 규칙

이 문서는 사람이 수기로 채우는 정적 문서가 아니라, Master Pipeline의 AI Analyze 단계(舊
WF-P05) 심층분석 결과 중 `significance`가 높은 건이 누적되면 주기적으로 요약을 반영하는
문서다 (자동 갱신은 Pilot 범위 밖이며, TASK-012 Dashboard가 이 역할의 상당 부분을 대체한다).
이 파일은 Claude Context에 로드되는 "확정된 배경지식" 용도로 유지한다.
