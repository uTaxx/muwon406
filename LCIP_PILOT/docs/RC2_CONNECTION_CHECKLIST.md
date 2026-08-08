# RC2 Connection Checklist — 실제 연결 실행 순서

Architect Review Round 12 TASK 3. RC1이 공식 승인되고 동결(Frozen)된 이후, RC2("Mock
기반 RC1을 실제 외부 데이터와 연결하여 실제 업무에서 검증 가능한 Pilot로 전환한다")
준비 단계에서 사용자가 실제로 무엇을 해야 하는지를 실행 순서로 단순화한 문서다.

`docs/CONNECTION_READINESS.md`(Round 7)를 대체하지 않는다 — Credential 발급처·OAuth
흐름 안내·Rollback Plan 같은 상세 내용은 그 문서를 그대로 따른다. 이 문서는 "무엇을,
어떤 순서로, 누가" 준비하는지만 사용자가 한눈에 보게 재정리한 것이다.

**이 문서를 읽거나 채워도 실제 외부 API 호출은 발생하지 않는다.** `config/
feature_flags.yaml`의 4개 스위치가 전부 `false`인 한 Pilot은 계속 Mock/dry-run으로
동작한다. 실제 연결은 사용자가 "Credential 준비 완료"를 알려준 다음 Round에서만
시작한다.

---

## A. 사용자가 해야 하는 일

Credential 발급·`.env` 입력·계정 설정 — Claude Code가 대신 수행하지 않는다(외부
계정 접근 권한이 없고, 시도해서도 안 된다).

1. §1 Credential 체크리스트의 각 항목을 발급받아 `.env`(Git에 커밋되지 않음)에
   직접 입력한다 — **Claude에게 실제 값을 절대 알려주지 않는다.** Claude에게는
   "N번 항목 준비 완료"라고만 알려주면 된다.
2. §2 RC2 연결 우선순위 순서대로 어디까지 준비됐는지 확인하고 알려준다(전부 한
   번에 갖출 필요 없음 — 1번부터 순서대로 진행 가능).
3. Google 인증 방식(Desktop OAuth vs Service Account)을 결정한다(§3 공동 확인
   항목이지만 최종 선택은 사용자 몫).
4. 각 연결을 실제로 켤 시점(Feature Flag를 `true`로 바꾸는 시점)을 Architect
   승인으로 명시적으로 지시한다.

## B. Claude가 해야 하는 일

Credential이 실제로 전달되기 전까지는 구조·코드만 준비한다 — 이 작업은 이미 Round
6~7에서 대부분 완료됐다(Provider Factory, Feature Flag, `enabled` 이중 게이트).

1. 사용자가 "N번 항목 준비 완료"라고 알려주면 해당 `.env` 키가 실제로 채워졌는지
   **값을 보지 않고** 존재 여부만 확인한다(`mask_secret()`으로 마스킹된 형태로만
   확인, `scripts/secret_scan.py`로 평문 유출 여부 검사).
2. Architect가 승인한 순서(§2)대로 `config/feature_flags.yaml`의 해당 스위치를
   `true`로 바꾸고, `docs/CONNECTION_READINESS.md` §5 Connection Test Plan에 정의된
   확인 방법으로 결과를 검증한다.
3. 문제가 생기면 즉시 해당 Flag를 다시 `false`로 되돌리고(Rollback Plan §6)
   원인을 보고한다 — 임의로 재시도하거나 다른 우회 방법을 시도하지 않는다.
4. 각 연결 전환 후 `python3 scripts/quality_gate.py`로 Mock Dependency 감소폭이
   의도한 범위인지 확인해 보고한다.

## C. 공동 확인이 필요한 일

- Google 인증 방식(Desktop OAuth vs Service Account) — 사용자 결정 사항이지만
  구조상 영향(코드 분기)이 있어 Claude가 트레이드오프를 설명한 뒤 확정한다.
- Claude 모델 ID 3종의 정확한 버전 — Anthropic Console에서 사용자가 확인한 값을
  Claude가 `config/model_registry.yaml`에 반영한다(비용/성능 조합은 함께 검토).
- 테스트 발송 수신 계정(이메일 주소, Telegram Chat ID) — 사용자가 지정하고,
  Claude가 `LCIP_TEST_EMAIL_RECIPIENT`/`TELEGRAM_CHAT_ID` 변수명이 맞는지 확인한다.
- 일일 비용 상한 도달 시 대응(§5 Rollback Plan 5번) — 임계값 수치는 사용자가
  `config/cost_policy.yaml` 기준으로 최종 승인하고, Claude가 `cost_guard.py` 동작을
  함께 확인한다.

---

## 1. Credential 체크리스트

Secret 값은 이 문서(또는 어떤 Markdown/코드/Git)에도 절대 기록하지 않는다 — `.env`
에만 저장한다(CLAUDE.md 절대 원칙 #7). "Claude에게 값을 직접 알려줘야 하는가" 열은
전 항목이 원칙적으로 **아니오**다 — Claude는 `.env` 키의 존재 여부만 마스킹된 형태로
확인하면 되고, 실제 문자열을 볼 필요가 없다.

| # | 항목 | 상태 | 필요 시점 | 필수/선택 | 입력 위치(`.env` 키) | Secret 여부 | Claude에게 값을 직접 알려줘야 하는가 |
|---|---|---|---|---|---|---|---|
| 1 | Anthropic API Key | 미준비 | RC2 1단계(최우선) | 필수 | `ANTHROPIC_API_KEY` | 예 | 아니오 — 준비 완료 여부만 |
| 2 | Claude model IDs 3종 | 미준비(`model_registry.yaml`에 `null`) | RC2 1단계, API Key와 함께 | 필수 | `LCIP_CLASSIFICATION_MODEL` / `LCIP_DEEP_ANALYSIS_MODEL` / `LCIP_FUTURE_READINESS_MODEL` | 아니오(모델 ID 문자열 자체는 비밀 아님) | 예 — 정확한 모델 ID는 Registry에 반영해야 하므로 문자열을 알려준다 |
| 3 | Google OAuth(Drive/Sheets/Gmail 공용) | 미준비 | RC2 2단계 | 필수(Drive/Sheets/Gmail 중 하나라도 켤 경우) | `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET`/`GOOGLE_OAUTH_TOKEN_PATH` 또는 `GOOGLE_SERVICE_ACCOUNT_JSON_PATH` | 예 | 아니오 |
| 4 | Google Drive Root Folder ID | 미준비 | RC2 2단계 | 필수(Drive 저장 시) | `GOOGLE_DRIVE_ROOT_FOLDER_ID` | 아니오(식별자, 비밀 아님) | 예 — 폴더 ID 문자열은 알려줘도 된다 |
| 5 | Google Sheets Master Spreadsheet ID | 미준비 | RC2 2단계 | 필수(Sheets 저장 시) | `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID` | 아니오(식별자, 비밀 아님) | 예 — Spreadsheet ID는 알려줘도 된다 |
| 6 | Google News RSS | 준비 불필요(공개 RSS, 인증 없음) | RC2 3단계 | 필수 | 해당 없음 | 아니오 | 해당 없음 |
| 7 | DART API Key | 미준비 | RC2 4단계 | 선택(국내 공시 확장 시) | `DART_API_KEY` | 예 | 아니오 |
| 8 | n8n Base URL | 미준비 | RC2 5단계(마지막) | 필수(자동배포 시) | `N8N_BASE_URL` | 아니오(URL, 비밀 아님) | 예 |
| 9 | n8n API Key | 미준비 | RC2 5단계 | 필수(자동배포 시) | `N8N_API_KEY` | 예 | 아니오 |
| 10 | Gmail Credential | 미준비 | RC2 6단계 | 선택(이메일 발송 시) | `GMAIL_SENDER_ADDRESS`/`GMAIL_OAUTH_CLIENT_ID`/`GMAIL_OAUTH_CLIENT_SECRET`/`GMAIL_OAUTH_TOKEN_PATH` | 예(Client Secret/Token) | 아니오 |
| 11 | Telegram Bot Token / Chat ID | 미준비 | RC2 7단계 | 선택(Telegram 발송 시) | `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` | Bot Token은 예, Chat ID는 아니오 | Chat ID만 예, Token은 아니오 |
| 12 | Naver API Client ID/Secret | 미준비 | RC2 8단계(마지막) | 선택(국내 뉴스 확장 시) | `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET` | 예 | 아니오 |

"상태"는 이 문서 작성 시점(Round 12) 기준이며, `.env.example`의 모든 값이 비어 있는
현재 상태를 그대로 반영한다 — 실제 준비 여부는 사용자가 §A-2로 갱신해 알려준다.

## 2. RC2 연결 우선순위 (Architect 지정 순서)

Round 12 지시대로 아래 8단계 순서를 Connection Test Plan의 기준으로 삼는다 — Round 7
`CONNECTION_READINESS.md` §5의 순서(RSS 우선)를 이 순서로 대체한다.

| 순서 | 대상 | Feature Flag | 관련 Credential(§1) |
|---|---|---|---|
| 1 | Claude API | `claude_api_enabled` | #1, #2 |
| 2 | Google Drive / Sheets | Sheets는 `google_sheets_enabled`. Drive는 별도 Feature Flag가 아직 없다 — `create_drive_structure.py --apply`(자체 dry-run/apply 스위치)로만 제어된다 | #3, #4, #5 |
| 3 | Google News RSS | `real_network_calls` | #6(준비 불필요) |
| 4 | DART | `real_network_calls` (어댑터 자체가 아직 stub — 구현이 선행) | #7 |
| 5 | n8n API | 해당 없음(n8n 자체 활성화) | #8, #9 |
| 6 | Gmail | `notification_send_enabled` | #10 |
| 7 | Telegram | `notification_send_enabled` | #11 |
| 8 | Naver News | `real_network_calls` (어댑터 자체가 아직 stub — 구현이 선행) | #12 |

각 단계 전환 후 확인 방법(스키마 통과 여부, 비용 확인 등)은 `docs/
CONNECTION_READINESS.md` §5의 기존 확인 방법을 그대로 따른다 — 순서만 이 표로
갱신됐다.

## 3. 실행 규칙 (변경 없음)

`docs/CONNECTION_READINESS.md` §1 원칙과 §6 Rollback Plan을 그대로 따른다 — 이
문서는 순서와 역할 분담만 재정리했을 뿐, 안전장치(Feature Flag 이중 게이트, 즉시
롤백)는 전혀 바꾸지 않았다.
