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

# Source Priority

> TASK-004B 산출물. Knowledge Base를 채우거나 Article/Intelligence를 검증할 때 어떤 출처를
> 먼저 신뢰할지에 대한 규칙이다. `schemas/article.schema.json`의 `source_reliability_grade`
> (A/B/C)와 `config/sources.yaml`의 `reliability_grade`가 이 문서의 등급 기준을 따른다.

## 1. 출처 우선순위 (조사·검증 순서)

Knowledge Base 작성 시(TASK-004A) 또는 Article의 사실관계를 교차검증할 때, 아래 순서로
출처를 확인한다. 상위 출처에서 확인된 사실이 하위 출처와 충돌하면 상위 출처를 우선한다.

1. **공식 홈페이지** (기업 자체 발표, 제품 페이지)
2. **사업보고서** (정기공시 — 사업의 내용, 위험요소 등)
3. **지속가능경영보고서** (ESG, 안전, 환경 공개 데이터)
4. **DART** (전자공시시스템 — 임시공시, 대량보유보고 등)
5. **IR 자료** (투자자 대상 설명자료, 실적발표)
6. **공식 보도자료** (기업이 직접 배포한 Press Release)
7. **정부자료** (정부기관 발표, 규제 공고, 법원 공개기록)
8. **언론** (신뢰할 수 있는 매체의 취재 보도)
9. **RSS** (Google News 등 자동 수집 — 1차 신호 탐지용, 단독 근거로는 신뢰도 낮음)

## 2. `source_reliability_grade` 매핑

| 등급 | 대응 출처 | 설명 |
|---|---|---|
| A | 공식 홈페이지, 사업보고서, 지속가능경영보고서, DART, IR, 공식 보도자료, 정부자료(1~7순위) | 1차 출처, 사실관계 오류 가능성 낮음 |
| B | 신뢰도 높은 주요 언론(8순위) | 2차 출처, 일반적으로 신뢰 가능하나 원출처 대조 권장 |
| C | RSS로만 수집되고 원출처 미상이거나, 신뢰도 낮은 매체(9순위) | 1차 신호 탐지용, 심층분석 전 반드시 상위 출처로 교차검증 |

## 3. 적용 규칙

- WF-P04(Rule Filter)의 `source_reliability_grade`는 `config/sources.yaml`의
  `reliability_grade`를 그대로 따른다 (Source 단위로 고정).
- 동일 사건에 대해 등급이 다른 여러 출처가 있으면, `evidence` 배열에 가능한 한 A/B 등급
  출처를 포함시킨다. C등급 출처만 있는 사건은 `confidence: low`로 표기한다.
- Knowledge Base(TASK-004A) 작성 시 새로운 사실을 추가할 때는 최소 A등급 출처 1개를
  `Source URL`로 명시해야 한다 (`KNOWLEDGE_POLICY.md` 참고).
