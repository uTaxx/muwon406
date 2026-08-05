# CLAUDE.md — LCIP Pilot 실행 지침

이 파일은 Claude Code가 `LCIP_PILOT/`에서 작업할 때 항상 먼저 읽어야 하는 프로젝트 헌법이다.

## 프로젝트 한 줄 정의

LCIP (LX Corporate Intelligence Platform) Pilot은 **공개정보만** 사용하여 LX홀딩스 전략팀의
**미래준비**(산업·정책·기술·M&A 신호 탐지)와 **리스크 관리**(소송·산업안전·통상·공급망 리스크
조기 감지)를 지원하는 개인용 Corporate Intelligence Pilot이다. 첫 작동 주제는
**엔지니어드스톤·실리코시스 리스크 모니터링** (`TOP-0001`, LX하우시스 관련).

일반 뉴스봇으로 축소 해석하지 말 것 — 모든 기능은 미래준비/리스크관리 미션과 LX 관련성 판단에
연결되어야 한다.

## 절대 원칙 (순서 무관, 전부 항상 적용)

1. 외부 **공개정보만** 사용한다. 내부 보고서·비공개 실적·미공개 거래정보·사내 메신저는 요구하거나
   추정하지 않는다.
2. 모든 핵심 사실에는 원문 URL을 저장한다.
3. 사실·AI 해석·AI 추론·제안을 명확히 구분한다.
4. 모든 분석은 LX홀딩스와 관련 계열사 관점에서 수행한다.
5. AI(Claude API)가 필요 없는 작업(정규화·중복제거·날짜필터·단순계산)에는 AI를 사용하지 않는다.
6. Claude API 월 사용액: 목표 **$15**, 절대 상한 **$20**. 개인 월 총비용(기존 구독 포함)
   **10만원 이하**.
7. Secret(API Key, OAuth Secret, Telegram Token, Chat ID 등)은 `.env` 또는 n8n Credential에만
   저장한다. 코드·Markdown·JSON·Google Sheets·Git에 평문 저장 금지.
8. 실제 외부 쓰기(Google Drive/Sheets 생성, n8n 배포, 이메일·Telegram 발송)는 사용자의 명시적
   승인 전까지 금지한다. 기본은 항상 `dry-run`.
9. n8n 워크플로우는 모듈형 Sub-workflow로 작성한다.
10. 변경 사항은 `CHANGELOG.md`와 관련 설계 문서에 반영한다.

## 작업 절차

1. 프로젝트 루트의 `CLAUDE.md`와 `docs/`의 연결 문서를 모두 읽는다.
2. 수정 전 현재 폴더 구조와 기존 파일을 검사한다.
3. 기존 파일이 있으면 덮어쓰지 말고 diff와 migration 계획을 제시한다.
4. Task는 `docs/03_BUILD_SPECIFICATION.md`의 TASK-001부터 순서대로, 선행 Task 의존성을 지켜
   실행한다.
5. 외부 계정에 영향을 주는 작업은 기본적으로 `dry-run`으로 구현한다.
6. 실제 Google Drive·Sheets 생성, n8n 배포, 이메일·Telegram 발송 전 사용자 승인을 요청한다.
7. Task 완료 후 `docs/05_ACCEPTANCE_TESTS.md`의 Acceptance Test를 수행한다.
8. 실패 시 다음 Task로 넘어가지 않는다.
9. 각 Task 완료 시 `PROJECT_STATUS.md`, `TODO.md`, `CHANGELOG.md`를 갱신한다.
10. 완료 주장은 생성 파일·테스트 결과·남은 사용자 작업을 제시한 뒤에만 한다.

## 먼저 읽을 문서 (읽는 순서)

1. `docs/01_PROJECT_CONTEXT.md`
2. `docs/02_SYSTEM_BLUEPRINT.md`
3. `docs/03_BUILD_SPECIFICATION.md` — 실행 명세서 (Task 정의의 최종 근거)
4. `docs/04_DATA_AND_CONFIG_SCHEMA.md`
5. `knowledge/PLATFORM_CONSTITUTION.md`, `knowledge/LX_HOLDINGS_CONTEXT.md`,
   `knowledge/LX_HAUSYS_COMPANY_DNA.md`, `knowledge/STRATEGY_PLAYBOOK.md`
6. `schemas/*.json`
7. `config/*.yaml`

파일이 없으면 Blueprint 기준으로 템플릿을 생성하되, 임의의 기업 사실은 작성하지 않고 TODO와
필요한 출처를 표시한다.

## 하지 말아야 할 것

- 과도한 프레임워크·추상화 도입
- 별도 DB(PostgreSQL 등)를 Pilot 단계에서 먼저 구축
- 모든 소스를 한 번에 연결
- 기사 원문 전체를 그대로 Claude에 전달 (요약·발췌만)
- Prompt를 n8n 노드 안에만 숨겨두기 (반드시 `prompts/*.md`로 버전관리)
- API Key 하드코딩
- 회사 내부정보를 요구하거나 추정
- 근거 없는 LX 영향 단정
- Pilot 단계에서 Enterprise 기능(다중사용자, 관리자포털, 전 계열사 자동화)까지 무리하게 구현

## 참고: 설계문서 간 알려진 충돌/불일치

`docs/04_DATA_AND_CONFIG_SCHEMA.md`의 "설계문서 충돌 로그" 절을 참고. 요약:

- 로컬 루트 폴더명·docs 구성은 `03_BUILD_SPECIFICATION.md`(이 폴더 구조) 기준을 따른다.
- Google Drive 폴더 구조는 `03_BUILD_SPECIFICATION.md` TASK-005 기준(`config/drive_structure.yaml`)을
  따르고, Blueprint의 8-폴더 구조는 참고용으로만 남긴다.
- Google Sheets 탭은 11개(`CHANGE_LOG` 포함) 모두 생성하되, 컬럼이 미문서화된 4개 탭은
  `config/sheet_structure.yaml`에 `status: draft`로 표시한다.
