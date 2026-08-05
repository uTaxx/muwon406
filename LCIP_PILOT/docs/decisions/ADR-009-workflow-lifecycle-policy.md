# ADR-009 — Workflow Lifecycle Policy

- **상태**: Accepted
- **날짜**: 2026-08-05
- **결정 주체**: Architect Review Round 4 Q1 (ChatGPT 검토, 사용자 승인 — Round 3의
  `deprecated_workflow_ids` 설계를 좋은 판단으로 승인하며 정식 정책으로 격상)

## 맥락

ADR-008(Workflow ID Policy)은 "ID는 영구 식별자이며 재배정하지 않는다"는 원칙만 정의했다.
Round 3에서 `config/workflow_registry.yaml`에 `deprecated_workflow_ids` 섹션을 임시로
추가해 결번(WF-P02~P07)을 문서화했는데, Round 4에서 이를 정식 Life Cycle 모델로 격상하기로
결정했다.

## 결정

모든 Workflow ID는 아래 3단계 Life Cycle 중 하나의 상태를 가진다.

```text
Active      — 현재 실행 중이거나 실행 대상인 워크플로우. n8n/workflows/*.json 파일이 존재.
    ↓ (기능이 다른 워크플로우로 흡수되거나 더 이상 트리거되지 않을 때)
Deprecated  — 물리적 파일은 없지만 ID와 과거 역할 기록은 영구 보존. 로그·문서에서 참조 가능.
    ↓ (Pilot 종료 또는 장기 미사용이 확정될 때, 선택적 단계)
Archived    — Deprecated 상태가 6개월 이상 지속되고 Enterprise 전환 계획에도 없을 때만 진입.
              문서 최하단으로 이동하되 여전히 삭제하지 않는다 (ID 영속성은 Archived에서도 유지).
```

### 상태 전이 규칙

- `Active → Deprecated`: 기능 통합/흡수 시 즉시 전이 (예: ADR-007의 WF-P02~P07).
- `Deprecated → Active`: 기능이 다시 분리되면 원래 ID로 복원 (ADR-008 원칙 그대로).
- `Deprecated → Archived`: 6개월 이상 미사용 + Enterprise 로드맵에 없음이 확인된 경우만.
  자동 전이 없음 — 분기별 검토(Knowledge Review Cycle과 동일 주기, `KNOWLEDGE_GOVERNANCE.md`
  §2 참고 패턴)에서 사람이 결정한다.
- `Archived → Active`: 가능하지만 드물어야 하며, 재도입 사유를 ADR로 남긴다.

### 현재 상태 (2026-08-05)

| 상태 | Workflow ID | 비고 |
|---|---|---|
| Active | WF-P01, WF-P08, WF-P09, WF-P10, WF-P99 | `n8n/workflows/*.json` 존재 |
| Deprecated | WF-P02, WF-P03, WF-P04, WF-P05, WF-P06, WF-P07 | Master Pipeline(WF-P01)에 흡수, ADR-007 |
| Archived | (없음) | 아직 Deprecated 6개월 경과 사례 없음 |

`config/workflow_registry.yaml`의 `deprecated_workflow_ids` 섹션에 `lifecycle_stage: deprecated`
필드를 추가해 이 상태를 기계가 읽을 수 있게 한다.

## 이유

- 단순히 "재배정 금지"만으로는 왜 특정 ID가 비어있는지, 다시 쓰일 가능성이 있는지 구분되지
  않는다. 3단계 모델은 "지금 당장은 안 쓰지만 언젠가 되살아날 수 있다"(Deprecated)와
  "사실상 완전히 종료됐다"(Archived)를 구분해 향후 판단을 쉽게 한다.
- Enterprise 전환 시 어떤 舊 기능을 되살릴지 검토할 때 이 상태값이 그대로 체크리스트가 된다.

## 트레이드오프

- 상태 전이를 수동으로 검토해야 하므로 관리 부담이 약간 늘어난다 → 분기 검토 주기에 편입해
  별도 절차를 만들지 않는다.

## 원복 가능성

가능. 이 정책 자체를 되돌려도 ADR-008의 "재배정 금지" 원칙은 유지된다 — Life Cycle 단계
구분만 없어질 뿐 ID 영속성은 그대로다.
