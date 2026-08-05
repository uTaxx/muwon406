# Changelog

모든 주요 변경사항을 이 파일에 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com/)를
느슨하게 따른다.

## [Unreleased]

### Added — TASK-001 ~ TASK-007 (2026-08-05)

- **TASK-001 Project Scaffold**: `LCIP_PILOT/` 전체 디렉터리 구조, `CLAUDE.md`, `README.md`,
  `.gitignore`, `.env.example`, `requirements.txt` 생성.
- **TASK-002 Core Configuration**: `config/*.yaml` 8개 파일 + `config/model_pricing.yaml`
  (Cost Guard 보조) 생성.
- **TASK-003 Data Schemas**: `schemas/*.schema.json` 6개 파일 생성 (JSON Schema Draft 2020-12).
- **TASK-004 Knowledge Templates**: `knowledge/*.md` 7개 템플릿 생성 (임의 사실 없이
  `TODO: source required` placeholder만 포함).
- **TASK-005 Google Drive Tooling**: `scripts/create_drive_structure.py` (dry-run 기본,
  `n8n_only` 인증모드에서는 어떤 외부 API도 호출하지 않음), `docs/GOOGLE_DRIVE_SETUP.md`.
- **TASK-006 Google Sheets Tooling**: `scripts/create_google_sheets.py` (dry-run 기본),
  `docs/GOOGLE_SHEETS_SETUP.md`, `schemas/google_sheets_columns.json` (11개 탭).
- **TASK-007 n8n Workflow Scaffold**: `n8n/workflows/WF-P01~P10, WF-P99.json` 11개 파일
  (전부 `active:false`, placeholder credential, Manual/Error Trigger 포함).
- 보조: `scripts/bootstrap_project.py`, `validate_config.py`, `secret_scan.py`,
  `cost_guard.py`, `source_health_check.py`, `claude_client.py`(stub),
  `build_dashboard.py`, `n8n_deploy.py`/`n8n_backup.py`/`n8n_list_workflows.py`(dry-run),
  `prompts/*.md` 6개, `dashboard/*`(template/styles/app.js/sample_data), `tests/*` 및
  fixtures, `docs/04_DATA_AND_CONFIG_SCHEMA.md`(설계문서 충돌 로그), `docs/05_ACCEPTANCE_TESTS.md`,
  `docs/decisions/ADR-001~005`.

### Notes

- 이번 라운드는 외부 API를 전혀 호출하지 않았다 (Google Drive/Sheets 실제 생성 없음, n8n 실제
  배포 없음, 이메일/Telegram 실제 발송 없음). 모든 관련 스크립트는 `--dry-run`이 기본값이다.
- 4개 설계문서(00_INITIAL_CLAUDE_CODE_HANDOVER, 01_LCIP_Pilot_System_Blueprint,
  02_LCIP_Pilot_Development_Manual, 03_BUILD_SPECIFICATION) 간 충돌 4건을 발견해
  `docs/04_DATA_AND_CONFIG_SCHEMA.md` §1에 기록하고 명시적으로 해소했다.
