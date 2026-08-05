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

# Knowledge Governance

> TASK-004C 산출물. "Knowledge 작성"이 아니라 "Knowledge Engine"을 운영하기 위한 거버넌스
> 규칙이다. Knowledge Base가 계속 신선하고 신뢰 가능한 상태를 유지하도록 버전·검토주기·
> 신뢰도·인용·충돌해결·아카이브 규칙을 정의한다.

## 1. Knowledge Version

- 모든 Knowledge 문서는 frontmatter `version:`을 갖는다 (예: `0.3`, `1.0`).
- 버전 규칙 (semantic-ish, 문서 규모에 맞게 단순화):
  - **Patch** (`0.1`→`0.2`): 문구 수정, 오탈자, 링크 갱신 등 구조 변경 없는 수정
  - **Minor** (`0.x`→`1.0`): 최초로 모든 계층에 실제 공개정보가 채워져 "draft"를 벗어날 때,
    또는 섹션이 추가/재배열될 때
  - **Major** (`1.x`→`2.0`): `knowledge_taxonomy_version`(현재 `1.0`) 자체가 바뀌어 문서
    구조를 다시 짜야 할 때
- `knowledge_taxonomy_version` frontmatter 필드로 어느 Taxonomy 버전을 따르는지 명시한다
  (현재 모든 회사 프로필 문서는 `1.0`).

## 2. Knowledge Review Cycle

`DEVELOPMENT_MANUAL_REFERENCE.md` §11 운영 점검 주기와 연동한다.

| 주기 | 점검 내용 |
|---|---|
| 매주 | 신규 Article이 기존 Knowledge와 상충하는 사실을 만들었는지 샘플 검토 |
| 매월 | 전체 회사 프로필 문서의 `Last Verified`가 §8 기준 임계값을 넘긴 항목 식별 |
| 매분기 | 전체 Knowledge Base 재검증 — 출처 링크 생존 여부, `confidence` 재평가 |
| Taxonomy 변경 시 | 전체 회사 프로필 문서 구조를 일괄 마이그레이션 (Major version bump) |

## 3. Knowledge Confidence Rule

각 항목(계층)의 `Confidence` 값은 아래 기준으로만 부여한다 — AI/사람 모두 임의로 상향하지
않는다.

| 값 | 기준 |
|---|---|
| `draft` | 아직 출처 미확인, 구조만 존재 (`TODO: source required`) |
| `low` | 출처는 있으나 2차 출처(언론 등, `SOURCE_PRIORITY.md` C등급)만 확보 |
| `medium` | B등급 출처 확보, 또는 A등급이지만 정보가 간접적/추정 포함 |
| `high` | A등급 1차 출처(공식 홈페이지/사업보고서/DART/IR 등)로 직접 확인 |

## 4. Source Citation Rule

- 모든 확정 사실(TODO가 아닌 항목)은 `Source`(출처 유형)와 `Reference URL`(원문 링크)을
  **예외 없이** 함께 가져야 한다 — 값 없이 confidence만 올리는 것을 금지한다.
- 출처 등급은 `SOURCE_PRIORITY.md`의 A/B/C 등급 체계를 그대로 사용한다.
- 인용 없는 문장은 게재하지 않는다 (`KNOWLEDGE_POLICY.md` §6과 동일 원칙의 구체화).

## 5. Conflict Resolution Rule

Knowledge Base 내부에서도 출처 간 사실이 상충할 수 있다 (예: 사업보고서와 언론 보도의
숫자가 다름).

1. `SOURCE_PRIORITY.md` 등급이 높은 출처를 우선 채택한다.
2. 등급이 같은 출처끼리 상충하면 **둘 다 기록**하고, 어느 쪽이 맞는지 단정하지 않는다 —
   해당 항목의 `Confidence`를 `low`로 낮추고 상충 사실을 문장에 명시한다.
3. Article/Intelligence 분석 중 발견된 상충은 `ANALYSIS_FRAMEWORK.md` §2의 동일 규칙을
   따른다 (Knowledge Base 자체의 상충과 Article 해석 중 상충을 같은 원칙으로 처리).

## 6. Evidence Priority

`SOURCE_PRIORITY.md`를 그대로 참조한다 (공식 홈페이지 → 사업보고서 → 지속가능경영보고서 →
DART → IR 자료 → 공식 보도자료 → 정부자료 → 언론 → RSS). 이 문서에서 별도로 재정의하지
않는다 — 단일 진실 공급원은 `SOURCE_PRIORITY.md` 하나로 유지한다.

## 7. Public Information Policy

- Knowledge Base에 반영 가능한 정보는 **공개적으로 접근 가능한 자료**로 한정한다: 공식
  홈페이지, 정기/수시 공시(DART), 지속가능경영보고서, IR 자료, 공식 보도자료, 정부기관
  발표, 신뢰할 수 있는 언론 보도, 법원 공개기록.
- 아래는 Knowledge Base에 반영하지 않는다: 사내 문서, 미공개 실적, 미공개 투자안, 사내
  메신저/이메일, 특정 개인을 식별하는 민감정보, 로그인/구독이 필요한 비공개 자료.
- 이 정책은 `CLAUDE.md` 절대 원칙 #1, `PLATFORM_CONSTITUTION.md` §1과 동일하며, 여기서는
  Knowledge Base 반영 시점의 구체적 체크리스트로 재확인한다.

## 8. Last Verified Policy

- 모든 확정 항목은 `Last Verified` 날짜를 가져야 한다.
- **신선도 임계값**: 회사 프로필 문서(COMPANY_DNA, HOLDINGS_CONTEXT)는 `Last Verified`로부터
  **6개월** 경과 시 재검증 대상으로 표시한다 (분기 재무·소송 진행 상황이 바뀔 수 있으므로
  Group Map류보다 짧게 잡는다). Framework/Policy류 문서(본 문서 포함)는 **12개월**.
- 임계값을 넘긴 항목은 `Confidence`를 자동으로 한 단계 낮추는 것을 권장한다 (`high`→`medium`
  등) — 실제 재검증 전까지 과신하지 않기 위함이다. 이 조정은 사람이 매분기 검토 시 수행한다
  (§2).

## 9. Archive Policy

- LCIP Pilot은 Knowledge 문서의 과거 버전을 **별도 archive 폴더에 복제하지 않는다** — Git
  이력 자체가 아카이브다 (`git log -p knowledge/<file>.md`로 모든 과거 버전 추적 가능).
- 예외: 대규모 Taxonomy Major 버전 변경(§1) 시점에는 변경 직전 상태에 Git 태그를 남긴다
  (예: `knowledge-v1.0-final`).
- `archive/` 디렉터리(로컬, gitignore 대상)는 Knowledge가 아니라 **대시보드/리포트 산출물**
  아카이브 전용이다 — Knowledge 문서를 그곳에 두지 않는다.

## 10. Knowledge Quality Score

회사 프로필 문서(16계층 Taxonomy 사용 문서)의 완성도를 정량화한다.

```text
Quality Score(%) = (신뢰 가능한 계층 수 / 12) × 100

"신뢰 가능한 계층" 조건 (셋 다 충족해야 함):
  1. Confidence가 draft가 아님 (low/medium/high 중 하나)
  2. Reference URL이 TODO/미확인이 아님
  3. Last Verified가 §8 신선도 임계값 이내

N/A로 표기된 계층(해당 없음)은 조건 없이 "신뢰 가능"으로 카운트한다 — 애초에 확인할
사실이 없기 때문이다.
```

측정 도구: `scripts/knowledge_quality.py`가 이 공식을 그대로 구현한다. Pilot 최초 구축
시점(리서치 착수 전)에는 모든 회사 프로필 문서의 Quality Score가 낮게 나오는 것이 정상이며,
이 숫자 자체가 "다음에 무엇을 리서치해야 하는지"에 대한 우선순위 신호로 쓰인다.
