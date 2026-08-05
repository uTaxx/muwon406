---
information_class: public
document_type: knowledge
company: LX Holdings
source_types: [DART, IR, official_website, sustainability_report]
reference_date:
last_reviewed: 2026-08-05
source_urls: []
confidence: draft
version: 0.2
owner: user
knowledge_taxonomy_version: 1.0
---

# LX Holdings Context

> TASK-004A(Knowledge Foundation Builder) 산출물. `knowledge/KNOWLEDGE_POLICY.md`의
> 16계층 Taxonomy를 지주회사 특성에 맞게 적용한다 (Product/Manufacturing/Raw Material은
> 지주회사 자체에는 해당하지 않으므로 생략하고, Company/Business/Government/Risk/
> Opportunity/Investment Point만 사용한다). `knowledge/KNOWLEDGE_POLICY.md` §4 우선순위
> 6위 문서.
>
> 본 문서는 공개정보로 확인된 사실만 기록한다. 아직 출처가 확인되지 않은 항목은 모두
> `TODO: source required`로 남겨두었으며, 임의로 채우지 않는다.

## 1. Company — 지주회사 개요·지배구조

- 설립 배경 및 지주사 전환 연혁: TODO: source required
- 본사 소재지: TODO: source required
- 상장 여부·거래소: TODO: source required
- 대표이사·이사회 구성: TODO: source required
- 지분 구조: TODO: source required (DART 대량보유 보고서 참고)
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

## 2. Business — 주요 계열사 (Portfolio)

- 계열사 목록 및 사업 분야: TODO: source required (DART 지배구조 공시 또는 공식 홈페이지 참고)
- 계열사별 매출 비중: TODO: source required
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

## 3. Government — 관련 규제·공시 체계

- 지주회사 관련 공시 의무(금융감독원/거래소 규정 등): TODO: source required
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

## 4. Risk — 재무·리스크 개요

- 최근 사업연도 연결 매출/영업이익: TODO: source required (DART 사업보고서)
- 재무 관련 공개 리스크 요인(공시상 "위험요소" 항목): TODO: source required
- 공식 발표된 ESG/리스크 관리 방향(리스크관리 축): TODO: source required (지속가능경영보고서 참고)
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

## 5. Opportunity — 전략 방향

- 공식 발표된 중장기 전략(미래준비 축): TODO: source required (IR 자료, 사업보고서 참고)
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

## 6. Investment Point — LX하우시스와의 관계

- 지분율 및 지배구조상 위치: TODO: source required
- 그룹 내 사업적 역할: TODO: source required
- Source: (미확인) / Reference URL: (미확인) / Confidence: draft / Last Verified: (미확인)

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
