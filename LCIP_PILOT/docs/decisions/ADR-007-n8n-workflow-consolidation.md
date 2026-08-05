# ADR-007 — n8n Workflow Consolidation (Master Pipeline)

- **상태**: Accepted
- **날짜**: 2026-08-05
- **결정 주체**: Architect Review Q4 (ChatGPT 검토, 사용자 승인)
- **우선순위 근거**: ADR-006에 따라 Architect Review의 명시적 지시가 03_BUILD_SPECIFICATION.md
  TASK-007 원안보다 우선 적용된다.

## 맥락

`03_BUILD_SPECIFICATION.md` TASK-007 원안은 WF-P01~P10 + WF-P99, 총 11개의 개별 n8n
워크플로우로 파이프라인을 구성했다. 이는 원칙(§ "모듈화": 수집·정규화·분류·분석·저장·발송을
분리)에는 부합하지만, n8n Cloud Starter 플랜의 실행 횟수 제한을 고려하면 Sub-workflow 호출이
누적되어 비용/한도 리스크가 커진다는 지적이 Architect Review에서 제기되었다.

## 결정

자동 파이프라인(수집→분석→대시보드→알림)을 **하나의 Master Pipeline 워크플로우**로 통합한다.
독립적으로 다른 스케줄/트리거를 가져야 하는 워크플로우만 분리 유지한다.

### 통합 후 구조 (5개 워크플로우)

| 파일 | 이름 | 트리거 | 비고 |
|---|---|---|---|
| `WF-P01-master-pipeline.json` | LCIP - Master Pipeline | Schedule(시간) + Manual | Config Load → News Collect → Rule Filter → AI Analyze → Dashboard → Notification → Logging → Finish를 단일 워크플로우 내 노드 체인으로 수행 |
| `WF-P02-source-health.json` | LCIP - Source Health | Schedule(6시간) + Manual | 기존 WF-P08과 동일 역할, 독립 스케줄 유지 |
| `WF-P03-cost-guard.json` | LCIP - Cost Guard | Sub-workflow + Manual | 기존 WF-P09과 동일 역할, Master Pipeline 및 다른 워크플로우에서 필요 시 호출 |
| `WF-P04-natural-language-admin.json` | LCIP - Natural Language Admin | Manual (관리자 수동 실행) | 기존 WF-P10과 동일 역할, 자동 스케줄 없음 → 실행 횟수에 영향 없음 |
| `WF-P99-error-handler.json` | LCIP - Error Handler | Error Trigger + Manual | 변경 없음 |

### 폐기(병합)된 개별 워크플로우

기존 `WF-P01-config-loader`, `WF-P02-news-collector`, `WF-P03-public-source-collector`,
`WF-P04-relevance-classifier`, `WF-P05-risk-analysis`, `WF-P06-dashboard-builder`,
`WF-P07-notification`은 별도 파일로 존재하지 않고, `WF-P01-master-pipeline.json` 내부의
노드 체인(Config Load / News Collect / Rule Filter / AI Analyze / Dashboard / Notification /
Logging)으로 흡수되었다. 각 단계의 역할·완료조건은 원본 TASK-007 정의와 동일하며, 물리적
워크플로우 경계만 사라졌다.

## 이유

- n8n Cloud Starter의 실행 횟수는 워크플로우 실행 1회당 카운트되며, Sub-workflow 호출도
  별도 실행으로 집계되는 경우가 많다. 8~9단계를 매번 개별 Sub-workflow로 호출하면 시간당
  실행 1건이 사실상 8~9건으로 증식한다.
- Source Health(6시간 간격)와 Cost Guard(다른 워크플로우에서 필요 시 조회)는 파이프라인과
  실행 주기·목적이 달라 독립 유지가 합리적이다.
- Natural Language Admin은 관리자가 수동으로만 실행하므로 자동 실행 횟수에 영향이 없어 분리
  유지해도 비용 리스크가 없다.
- Error Handler는 다른 모든 워크플로우의 `settings.errorWorkflow`가 참조하는 공통 처리기이므로
  분리 구조가 필수적이다.

## 트레이드오프

- Master Pipeline 내부 노드 수가 많아져 워크플로우 하나의 복잡도가 높아진다 → 노드 이름과
  `notes` 필드로 각 단계 역할을 명확히 표기해 가독성을 보완한다.
- 특정 단계(예: Dashboard Builder)만 재실행하고 싶을 때 전체 파이프라인을 다시 돌려야 한다
  → Pilot 단계에서는 수용 가능한 트레이드오프로 판단 (Enterprise 전환 시 재분리 검토).

## 원복 가능성

가능. `config/workflow_registry.yaml`과 `n8n/workflows/`를 TASK-007 원안(11개 파일)으로
되돌리면 복원된다. 각 노드의 역할 정의 자체는 바뀌지 않았으므로 재분리 시 로직 손실은 없다.
