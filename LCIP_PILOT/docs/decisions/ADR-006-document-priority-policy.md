# ADR-006 — Document Priority Policy

- **상태**: Accepted
- **날짜**: 2026-08-05
- **결정 주체**: Architect Review (ChatGPT 검토, 사용자 승인)

## 맥락

Google Drive의 4개 설계문서(`00_INITIAL_CLAUDE_CODE_HANDOVER.md`, `01_LCIP_Pilot_System_Blueprint.md`,
`02_LCIP_Pilot_Development_Manual.md`, `03_BUILD_SPECIFICATION.md`) 사이에 로컬 폴더 구조,
Google Drive 폴더 구조, Google Sheets 탭 개수, SOURCE_HEALTH 필드명 등 4건의 불일치가
발견되었다 (`docs/04_DATA_AND_CONFIG_SCHEMA.md` §1 참고). TASK-001~007 구현 시점에는
"실행 명세서 우선" 원칙으로 임시 해결했으나, 향후에도 반복될 충돌에 대비해 공식적인
우선순위를 고정할 필요가 있었다.

## 결정

Project Bible(4개 설계문서) 우선순위를 다음과 같이 고정한다.

| 순위 | 문서 | 역할 |
|---|---|---|
| 1 | `docs/03_BUILD_SPECIFICATION.md` | Implementation Truth (실행 명세) |
| 2 | `docs/02_SYSTEM_BLUEPRINT.md` | Architecture Truth (아키텍처 원칙) |
| 3 | `docs/DEVELOPMENT_MANUAL_REFERENCE.md` (원본: `02_LCIP_Pilot_Development_Manual.md`) | Development Guideline (개발 관행) |
| 4 | `docs/01_PROJECT_CONTEXT.md` (원본: `00_INITIAL_CLAUDE_CODE_HANDOVER.md`) | Project History (최초 핸드오버 배경) |

앞으로 문서 간 내용이 충돌하면 반드시 **BUILD_SPECIFICATION → SYSTEM_BLUEPRINT →
DEVELOPMENT_MANUAL → HANDOVER** 순으로 우선 적용한다. 단, 상위 문서보다 더 높은 권한을
가진 것은 **Architect Review(사용자 승인을 거친 명시적 지시)** 뿐이며, Architect Review가
명시적으로 하위 문서 내용이나 새로운 결정을 채택하라고 지시하면 그 지시가 최우선이다
(예: ADR-007의 n8n Workflow 통합 결정은 03_BUILD_SPECIFICATION.md TASK-007의 원안(11개
개별 워크플로우)보다 우선 적용된다).

## 이유

- 실행 코드와 가장 밀접한 문서(BUILD_SPECIFICATION)를 최우선으로 두면 "무엇을 만들어야
  하는가"에 대한 모호함이 줄어든다.
- 나머지 문서는 각각 아키텍처 배경, 개발 관행, 프로젝트 이력이라는 명확히 다른 역할을 가지므로
  순서를 고정해도 정보 손실이 없다 (모든 원문은 `docs/`에 그대로 보존됨).
- Architect Review에 최우선권을 부여함으로써, 설계문서 자체를 매번 다시 쓰지 않고도 프로젝트를
  살아있는 상태로 개선할 수 있다.

## 트레이드오프

- 원본 4개 문서 자체는 갱신하지 않고 그대로 보존하므로, 실제 구현 상태와 원본 문서 사이에
  괴리가 생길 수 있다 → 괴리가 발생할 때마다 `docs/04_DATA_AND_CONFIG_SCHEMA.md`의 충돌
  로그와 관련 ADR에 반드시 기록한다.
