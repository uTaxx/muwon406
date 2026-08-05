# 05. Acceptance Tests — TASK-001 ~ TASK-007

`03_BUILD_SPECIFICATION.md`의 각 TASK 완료조건을 실행 가능한 체크리스트로 정리한 것. 각
TASK는 여기 나열된 조건을 모두 통과해야 "완료"로 보고할 수 있다 (§23 공통 Definition of Done).

## TASK-001 Project Scaffold

- [ ] `find LCIP_PILOT -type d`로 `03_BUILD_SPECIFICATION.md` §3의 모든 폴더 존재 확인
- [ ] `.gitignore`에 필수 항목(.env, credentials*.json, token*.json, *.key, *.pem 등) 포함
- [ ] `python scripts/bootstrap_project.py --dry-run` 종료 코드 0
- [ ] 재실행 시 기존 파일 덮어쓰지 않음 (idempotent) — 동일 명령 2회 연속 실행해 diff 없음 확인

## TASK-002 Core Configuration

- [ ] `config/*.yaml` 8개 파일 모두 존재
- [ ] `python scripts/validate_config.py` 종료 코드 0 (YAML 문법, 필수값, ID 중복 없음)
- [ ] Secret 관련 키(API Key 등)가 YAML 안에 값으로 존재하지 않음 (`scripts/secret_scan.py` 통과)

## TASK-003 Data Schemas

- [ ] `schemas/*.schema.json` 6개 파일 모두 유효한 JSON Schema (Draft 2020-12 호환)
- [ ] `pytest tests/test_schema.py` 통과 — 정상 fixture 통과, 비정상 fixture(필수필드 누락) 거부
- [ ] `average_amount_per_person_usd` null 허용 검증 (총액/원고수 없을 때)

## TASK-004 Knowledge Templates

- [ ] `knowledge/*.md` 7개 파일 모두 존재, 공통 YAML frontmatter 포함
- [ ] 임의의 확정 회사 사실 없음 — 미확인 내용은 전부 `TODO: source required`로 표시
- [ ] heading 구조가 있어 Claude Context로 부분 로드 가능

## TASK-005 Google Drive Tooling

- [ ] `python scripts/create_drive_structure.py --dry-run` 성공, 생성 예정 폴더 목록만 출력
- [ ] `--apply` 플래그 없이는 어떤 Google API도 호출하지 않음 (코드 검사로 확인)
- [ ] 3가지 인증 방식(OAuth Desktop / Service Account / n8n Credential only) 선택 가능한 구조
- [ ] Secret(클라이언트 시크릿 등)이 로그에 출력되지 않음

## TASK-006 Google Sheets Tooling

- [ ] `python scripts/create_google_sheets.py --dry-run` 성공, 생성 예정 탭·컬럼만 출력
- [ ] `--apply` 없이는 Sheets API 호출 없음
- [ ] `schemas/google_sheets_columns.json`과 `config/sheet_structure.yaml` 컬럼 일치
- [ ] 기존 Spreadsheet ID가 있을 때 "누락분만 생성" 로직 존재 (코드 리뷰로 확인, 실호출은 생략)

## TASK-007 n8n Workflow Scaffold

- [ ] `n8n/workflows/*.json` 11개 파일 모두 유효한 JSON
- [ ] 전부 `"active": false`
- [ ] Credential은 이름(placeholder)만 참조, ID 하드코딩 없음
- [ ] 각 워크플로우에 Manual Trigger 노드와 Error 분기(WF-P99 참조 또는 자체 처리) 포함
- [ ] `pytest tests/test_n8n_json.py` 통과

## 공통 (모든 TASK)

- [ ] `python scripts/secret_scan.py` 전체 저장소 대상 종료 코드 0
- [ ] `PROJECT_STATUS.md` / `TODO.md` / `CHANGELOG.md` 최신 상태 반영
- [ ] 사용자가 해야 할 남은 작업(계정 준비, 승인 등)이 `TODO.md`에 명시됨
