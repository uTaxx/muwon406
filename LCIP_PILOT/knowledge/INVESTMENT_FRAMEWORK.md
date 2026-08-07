---
information_class: public
document_type: framework
company:
source_types: []
reference_date:
last_reviewed: 2026-08-07
source_urls: []
confidence: high
version: 1.0
owner: Architect Review (2026-08-05)
---

# Investment Framework

> TASK-004B 산출물. 미래준비(`future_readiness`) 축 분석과 기업 Quick Scan(`prompts/quick_scan.md`)
> 이 따르는 평가 기준이다. Knowledge Taxonomy(`KNOWLEDGE_POLICY.md`)의 12번 항목
> "Investment Point"를 채우는 기준이기도 하다.

## 1. 대상 신호 유형 (MISSION_FRAMEWORK.md future_readiness 서브카테고리와 동일)

- **M&A**(`ma`): 인수합병 — 지분 인수, 완전 합병 등
- **Carve-out**(`carve_out`): 사업부 분리매각
- **Bolt-on**(`bolt_on`): 기존 사업 보강형 소규모 인수
- **JV**(`jv`): 합작법인 설립
- **Venture**(`venture`): 스타트업/신규 법인 지분투자
- **Capital Market**(`capital_market`): 자본시장 환경 변화(금리, 밸류에이션 등)
- **Technology**(`technology`): 대체·신소재 기술, 공정 혁신
- **New Business**(`new_business`): 신사업 진출 신호

## 2. Quick Scan 평가 항목 (Investment Point)

기업 Quick Scan(`prompts/quick_scan.md`)이 산출하는 `opportunity_signal_type`과 함께,
아래 관점을 공개정보 범위 내에서 평가한다.

| 평가 항목 | 설명 |
|---|---|
| 사업 적합성 | LX 기존 사업(Value Chain)과의 연관성/시너지 |
| 시장 지위 | 대상 기업의 경쟁사 대비 위치 (공개 자료 기준) |
| 성장성 신호 | 공개된 실적/투자 유치 이력 등 |
| 리스크 요인 | 대상 기업의 공개된 리스크(소송, 규제 등) |
| 자금 규모 추정 근거 | 공개된 거래 규모/밸류에이션 정보 (없으면 명시적으로 "비공개") |
| 추가 조사 필요 사항 | Quick Scan만으로 판단 불가능한 부분 |

## 3. 절대 규칙

- **사용자가 명시적으로 지정한 기업만** Quick Scan 대상으로 삼는다 (`prompts/quick_scan.md`와
  동일 원칙). 임의로 M&A 후보를 탐색·제안하지 않는다.
- 비공개 협상 정보, 미공개 재무 수치를 추정하지 않는다.
- 투자 여부에 대한 최종 판단은 내리지 않는다 — "투자검토 기초자료"까지만 제공한다
  (`03_BUILD_SPECIFICATION.md` §0 미래준비 정의와 동일).

## 4. Pilot 범위 안내

Architect Review Round 5부터 Quick Company Scan이 Pilot의 첫 번째 실제 서비스로
승격되었고, 그 출력이 `scripts/investment_review.py`(Investment Review Engine)의 입력으로
연결되었다 (`scripts/quick_company_scan.py:build_investment_review_input()`). Pilot
범위의 Valuation은 **Comparable(비교기업 배수) 기반으로만** 계산한다 — 이 문서의
"최종 투자판단을 내리지 않는다"는 원칙은 그대로 유지된다.

**Enterprise Backlog(Pilot에서 구현하지 않음)**: DCF(Round 5 명시), LBO/Option/
PMI(Post-Merger Integration)(Architect Review Round 9 "Pilot에서 사용하지 않는 DCF/LBO/
Option/PMI 등은 Backlog로 이동한다. 구현하지 않는다" 재확인). 네 항목 모두 지금까지
구현된 적이 없다 — Comparable 기반만 유지하기로 한 결정을 다시 확인한 것이며, 코드
변경이 필요한 항목이 아니다.
