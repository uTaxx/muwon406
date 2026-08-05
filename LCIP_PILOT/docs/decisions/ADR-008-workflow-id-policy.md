# ADR-008 — Workflow ID Policy

- **상태**: Accepted
- **날짜**: 2026-08-05
- **결정 주체**: Architect Review Round 3 Q1 (ChatGPT 검토, 사용자 승인)
- **번복 대상**: Architect Review Round 2(Q4)의 n8n 워크플로우 재구성(ADR-007) 직후, 통합된
  5개 워크플로우에 `WF-P01~P04` 번호를 촘촘하게 재배정했던 결정을 되돌린다.

## 맥락

ADR-007(Round 2)에서 11개 워크플로우를 5개(Master Pipeline, Source Health, Cost Guard,
Natural Language Admin, Error Handler)로 통합하면서, 남은 5개에 번호를 `WF-P01~P04, P99`로
촘촘히 재배정했다. Round 3 검토에서 이 재배정이 문제로 지적되었다: **Workflow ID는 영구
식별자**이며, 향후 Enterprise 단계에서 워크플로우가 추가/재분리될 때 번호가 이미 다른 워크플로우
(예: 舊 WF-P02 News Collector)에 쓰였던 이력이 있으면 참조·로그·백업 이력에서 혼선이 생긴다.

## 결정

**Workflow ID는 한 번 부여되면 재배정하지 않는다.** 기능이 통합되어 특정 번호가 물리적으로
빈 파일이 되더라도, 그 번호를 다른 역할에 재사용하지 않는다.

ADR-007 통합 이후 최종 ID는 다음과 같이 **원래 번호로 유지**한다.

| Workflow ID | 파일 | 역할 |
|---|---|---|
| `WF-P01` | `n8n/workflows/WF-P01-master-pipeline.json` | Master Pipeline (舊 WF-P01~P07 기능 통합) |
| `WF-P08` | `n8n/workflows/WF-P08-source-health.json` | Source Health (원래 번호 유지) |
| `WF-P09` | `n8n/workflows/WF-P09-cost-guard.json` | Cost Guard (원래 번호 유지) |
| `WF-P10` | `n8n/workflows/WF-P10-natural-language-admin.json` | Natural Language Admin (원래 번호 유지) |
| `WF-P99` | `n8n/workflows/WF-P99-error-handler.json` | Error Handler (변경 없음) |

`WF-P02`~`WF-P07`은 Master Pipeline으로 흡수되어 더 이상 별도 파일로 존재하지 않지만, 그
번호를 다른 워크플로우에 재사용하지 않는다 — 결번(deprecated) 상태로 영구히 남긴다. 향후
Enterprise 단계에서 해당 기능이 다시 분리되면 원래 번호(WF-P02 News Collector 등)를 그대로
복원해서 쓴다.

## 이유

- **ID의 영속성 > 번호의 연속성.** 로그, 백업 이력(`n8n/backups/`), COST_LOG/ERROR_LOG의
  `workflow_id` 컬럼, 외부 모니터링 도구가 Workflow ID를 키로 참조한다. 번호를 재배정하면
  과거 로그의 `workflow_id`가 가리키는 대상이 시점에 따라 달라지는 모순이 생긴다.
- Enterprise 확장 시 결번 구간(WF-P02~P07)에 원래 의미 그대로 워크플로우를 복원할 수 있어
  마이그레이션이 단순해진다.

## 트레이드오프

- 활성 워크플로우 5개의 번호가 `01, 08, 09, 10, 99`로 연속적이지 않아 목록만 봐서는 다소
  듬성듬성해 보인다 → `config/workflow_registry.yaml`과 `docs/decisions/ADR-007-n8n-workflow-consolidation.md`
  표에 결번 사유를 명시해 혼란을 방지한다.

## 원복 이력

Round 2(ADR-007 직후)에 `WF-P02~WF-P04`로 재배정했던 이력이 있다. 이 ADR로 원래 번호
(`WF-P08~WF-P10`)로 되돌렸다. **이후로는 이 정책에 따라 재배정하지 않는다.**
