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

# Analysis Framework

> TASK-004B 산출물. Master Pipeline의 AI Analyze 단계(舊 WF-P05 Risk Analysis, ADR-007로
> 통합)가 Article을 분석할 때 따르는 절차와, Knowledge Taxonomy(`KNOWLEDGE_POLICY.md`)·
> Mission Framework(`MISSION_FRAMEWORK.md`)를 어떻게 연결하는지 정의한다.

## 1. 분석 절차

```text
Article 원문
→ (1) Rule Filter 결과 확인 (관련성, 1차 mission 후보)
→ (2) 관련 Knowledge 발췌 (KNOWLEDGE_POLICY.md 16계층 중 관련 항목만 — 전체 KB 전송 금지)
→ (3) 사실 추출 (facts) — 원문에서 직접 확인 가능한 것만
→ (4) Knowledge Taxonomy 매핑 — 이 사실이 Business/Product/Manufacturing/
     Value Chain/Customer/Competitor/Raw Material/Government/Risk/Opportunity/
     Investment Point 중 어디에 해당하는지 식별
→ (5) Mission 매핑 — MISSION_FRAMEWORK.md 기준 mission + mission_subcategory 결정
→ (6) LX 영향(lx_impact) 판단 — Knowledge에 실제 근거가 있을 때만
→ (7) 대응/추가조사(actions) 제안
→ (8) 미확인 사항(unknowns) 기록
→ (9) JSON Schema(claude_output.schema.json) 검증
```

## 2. Knowledge Taxonomy 매핑 규칙

Article의 사실이 Knowledge Taxonomy(16계층 중 1~12)의 어느 항목과 연결되는지 판단할 때:

- 사실이 **기존 Knowledge 문서의 내용과 일치**하면 → 해당 계층을 그대로 인용 (근거 링크는
  Article 원문 URL과 Knowledge 문서 내 출처 URL 둘 다 남긴다).
- 사실이 **기존 Knowledge에 없는 새로운 정보**이면 → `unknowns`에 "Knowledge Base 갱신 필요"
  로 표시하고, 임의로 Knowledge를 덮어쓰지 않는다 (Knowledge 갱신은 사람이 검토 후 수행).
- 사실이 **기존 Knowledge와 상충**하면 → `unknowns`에 상충 사실을 명시하고 `confidence`를
  낮춘다. 자동으로 어느 쪽이 맞는지 판단하지 않는다.

## 3. Mission 매핑 규칙

- `MISSION_FRAMEWORK.md`의 두 축(미래준비/리스크관리) 중 하나 이상에 반드시 매핑한다.
- 서브카테고리가 명확하지 않으면 `mission_subcategory: null` + `unknowns`에 사유 기록.
- 하나의 Article이 복수 축에 걸치는 경우(예: 규제 강화가 리스크이자 동시에 경쟁사 대비
  기회) `mission`은 **가장 중요도가 높은 축 하나**를 선택하고, 다른 축의 시사점은
  `recommended_actions`에 별도로 남긴다 (Pilot 단계 단순화 — Enterprise에서 다중 태깅
  검토).

## 4. 심각도(significance) 판단 — STRATEGY_PLAYBOOK.md 연동

`significance`는 `knowledge/STRATEGY_PLAYBOOK.md` §2 "리스크 대응 우선순위 판단 기준"의
긴급/중요/참고 3단계 기준을 그대로 사용한다.

## 5. Investment Point (미래준비 축 전용)

미래준비 축으로 분류된 Article은 `lx_impact` 대신(또는 추가로) 아래 관점을 검토한다 —
`knowledge/INVESTMENT_FRAMEWORK.md` 기준.

## 6. 출력 시 근거 표기

모든 사실에는 원문 URL(`evidence`)을 포함하고, Knowledge Taxonomy를 인용한 경우 어떤
Knowledge 문서의 어떤 섹션을 참조했는지 `ai_interpretation`에 명시한다 (예: "LX_HAUSYS_
COMPANY_DNA.md §9 미국 사업 노출 참고").
