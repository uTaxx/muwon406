# Google Sheets Setup — LCIP Pilot

TASK-006 산출물. `scripts/create_google_sheets.py`를 실제로 실행(`--apply`)하기 전에
아래 준비가 필요하다.

## 1. 기존 Master Spreadsheet 존재 여부 확인 (§24 질문 #3)

이미 만들어둔 Master Spreadsheet가 있다면 ID를 `.env`의
`GOOGLE_SHEETS_MASTER_SPREADSHEET_ID`에 넣는다. 없다면 최초 생성이 필요하다.

## 2. dry-run 실행

```bash
cd LCIP_PILOT
python scripts/create_google_sheets.py --dry-run
```

`config/sheet_structure.yaml` + `schemas/google_sheets_columns.json`을 읽어 생성할 탭과
컬럼만 출력한다. 어떤 외부 API도 호출하지 않는다.

기존에 이미 만들어둔 탭이 있다면 `--existing-tabs "CONFIG_MASTER,TOPIC_CONFIG"`처럼 전달해
시뮬레이션할 수 있다 — 이미 있는 탭은 "생성 예정"에서 제외되고 데이터도 건드리지 않는다.

## 3. Draft 상태 탭 안내

11개 탭 중 `SENT_HISTORY`, `ERROR_LOG`, `CHANGE_REQUEST`, `CHANGE_LOG` 4개는 원본 설계문서
3개(Build Specification/Development Manual/System Blueprint) 사이에 컬럼 정의가 없거나
서로 달라, 이번 라운드에서 문맥상 합리적으로 초안 작성했다 (`docs/04_DATA_AND_CONFIG_SCHEMA.md`
§3 참고). 실제 생성 전에 컬럼 구성을 검토해달라.

## 4. 실제 생성 (사용자 승인 후에만)

```bash
export LCIP_CONFIRM_APPLY=yes
python scripts/create_google_sheets.py --apply
```

이번 라운드에서는 `--apply`를 붙여도 실제 Sheets API를 호출하지 않고, TASK-008 이후 라운드로
안내 메시지만 출력한다 (Google 인증정보 준비 + 사용자 명시적 승인이 선행되어야 하므로).

## 5. 생성될 탭 목록

`config/sheet_structure.yaml` 참고: `CONFIG_MASTER, TOPIC_CONFIG, SOURCE_REGISTRY, ARTICLE_DB,
INTELLIGENCE_DB, SOURCE_HEALTH, COST_LOG, SENT_HISTORY, ERROR_LOG, CHANGE_REQUEST, CHANGE_LOG`
(총 11개).
