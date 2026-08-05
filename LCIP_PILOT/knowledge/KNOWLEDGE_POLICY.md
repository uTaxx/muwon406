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

# Knowledge Policy

> TASK-004B 산출물. Knowledge Base(`knowledge/*.md`)를 어떻게 구성·작성·검증할지에 대한
> 정책 문서다. TASK-004A(Knowledge Foundation Builder)는 이 문서의 규칙을 따른다.

## 1. Knowledge는 "회사소개"가 아니다

Knowledge Base는 단순 회사 소개 문서가 아니라, **AI(Claude)가 LX를 이해하고 Article을
LX 관점에서 해석할 수 있게 만드는 구조화된 지식**이다. 모든 회사 관련 Knowledge 문서는
아래 16계층 Taxonomy를 따른다.

## 2. Knowledge Taxonomy (16계층)

```text
1.  Company           — 법인 개요, 지배구조, 연혁
2.  Business           — 사업 포트폴리오, 사업부 구성
3.  Product             — 주요 제품/브랜드
4.  Manufacturing       — 생산 거점, 생산 공정
5.  Value Chain         — 원재료→생산→유통→고객 흐름
6.  Customer            — 고객 산업, B2B/B2C 구조
7.  Competitor          — 경쟁사, 시장 지위
8.  Raw Material        — 주요 원재료, 조달 구조
9.  Government          — 관련 정부/규제기관, 인허가
10. Risk                — 리스크 요인 (Mission Framework의 risk_management 축과 연결)
11. Opportunity         — 성장 기회 (Mission Framework의 future_readiness 축과 연결)
12. Investment Point     — 투자검토 관점의 핵심 포인트 (Quick Scan/M&A 신호와 연결)
13. Source               — 위 1~12 각 항목의 근거 출처
14. Reference URL        — 근거 원문 링크
15. Confidence           — 출처 신뢰도 (high/medium/low/draft)
16. Last Verified        — 마지막 확인 일자
```

13~16번(Source/Reference URL/Confidence/Last Verified)은 **1~12번 각 항목마다 개별적으로**
붙는 메타데이터다 — 문서 전체에 한 번만 붙이는 것이 아니라, 각 사실 단위로 근거를 추적할 수
있어야 한다.

## 3. 문서별 항목 서식

각 Knowledge 항목은 아래 형식을 따른다.

```markdown
### [번호]. [계층 이름] — [세부 주제]

[내용 — 확인된 사실만. 미확인 시 "TODO: source required"]

- Source: [출처 유형, 예: 사업보고서 / DART / 공식 홈페이지]
- Reference URL: [원문 URL, 미확인 시 TODO]
- Confidence: [high | medium | low | draft]
- Last Verified: [YYYY-MM-DD, 미확인 시 TODO]
```

## 4. Knowledge 파일 우선순위 (Architect Review Q6, 2026-08-05 확정)

Knowledge Base를 채우는(TASK-004A 이후 실제 리서치) 순서는 다음과 같다. TOP-0001(엔지니어드
스톤·실리코시스) 리스크 분석에 대한 기여도가 높은 순서다.

| 순위 | 파일 | 이유 |
|---|---|---|
| 1 | `LX_HAUSYS_COMPANY_DNA.md` | TOP-0001의 직접 분석 대상 |
| 2 | `LX_HAUSYS_VALUE_CHAIN.md` | 리스크 전이 경로 분석의 기초 |
| 3 | `GROUP_RISK_MAP.md` | 리스크 카테고리·현황 종합 |
| 4 | `GROUP_OPPORTUNITY_MAP.md` | 미래준비 축 신호 종합 |
| 5 | `STRATEGY_PLAYBOOK.md` | 판단 기준(긴급/중요/참고 분류) |
| 6 | `LX_HOLDINGS_CONTEXT.md` | 지주사 배경 — 계열사 분석의 전제 |
| 7 | `PLATFORM_CONSTITUTION.md` | 플랫폼 자체 규정 (이미 완성, 회사 사실 아님) |

이 순서는 `CLAUDE.md`의 "먼저 읽을 문서" 섹션에도 반영되어 있다.

## 5. 출처 확인 순서

`SOURCE_PRIORITY.md`를 따른다 (공식 홈페이지 → 사업보고서 → 지속가능경영보고서 → DART →
IR 자료 → 공식 보도자료 → 정부자료 → 언론 → RSS).

## 6. 절대 규칙 (기존 원칙과 동일, 재확인)

- 공개정보로 확인되지 않은 사실을 작성하지 않는다.
- 확인되지 않은 항목은 반드시 `TODO: source required`로 표시하고, 임의로 채우지 않는다.
- 사실과 AI 해석/추론을 구분한다 (Risk/Opportunity/Investment Point 항목은 특히 "사실"과
  "판단"을 분리해서 기록한다).
