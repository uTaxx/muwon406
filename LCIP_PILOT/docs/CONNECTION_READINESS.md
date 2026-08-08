# Connection Readiness (Architect Review Round 7)

> Round 7 지시: "현재부터 실제 API 연결 준비를 시작한다. 다음 라운드에서는 API를 호출하지
> 말고 Connection Readiness만 준비한다 ... 실제 호출은 Architect 승인 이후 진행한다."
>
> 이 문서는 **실제 외부 호출을 하지 않는다.** Credential 발급 안내, 환경변수 목록,
> 연결 테스트 계획, 롤백 계획만 다룬다. 이 문서를 읽고 따라 해도 `config/
> feature_flags.yaml`의 4개 스위치가 전부 `false`인 한 실제 네트워크 호출은 발생하지
> 않는다 — 그것이 Round 6에서 만든 Feature Flag 아키텍처의 목적이다.

## 1. 원칙

1. 이 문서의 어떤 단계도 사용자의 명시적 승인 없이 실행하지 않는다.
2. Credential(API Key/OAuth Secret/Token)은 `.env`에만 저장한다 — Git/Markdown/Google
   Sheets/코드에 평문 저장 금지(`CLAUDE.md` 절대 원칙 #7, `scripts/secret_scan.py`로 검사).
3. 연결은 한 번에 하나씩, 가장 위험이 낮은 것부터 켠다(§5 Connection Test Plan 순서).
4. 문제가 생기면 코드를 고치기 전에 먼저 `config/feature_flags.yaml`을 `false`로
   되돌린다(§6 Rollback Plan) — 이것이 이 아키텍처의 유일하고 가장 빠른 킬스위치다.

## 2. Credential 체크리스트 (시스템별)

| 시스템 | 필요한 것 | 발급처 | 이 Pilot에서의 사용처 |
|---|---|---|---|
| Anthropic Claude | API Key | Anthropic Console | `ClaudeProvider._call_anthropic()` |
| Anthropic 모델 ID 3종 | 모델 ID 문자열(Haiku/Sonnet/Opus 계열) | Anthropic Console | `config/model_registry.yaml` |
| Google Drive | OAuth Client(Desktop) 또는 Service Account | Google Cloud Console | TASK-005(dry-run만 구현됨) |
| Google Sheets | 위와 동일 + Master Spreadsheet ID | Google Cloud Console | `GoogleSheetsStorage` |
| n8n Cloud | Base URL + API Key | n8n Cloud 계정 설정 | TASK-008(아직 미착수, 마지막 순위) |
| Gmail | OAuth Client + 발신 계정 | Google Cloud Console | `EmailNotifier` 실제 발송 |
| Telegram | Bot Token + Chat ID | @BotFather | `TelegramNotifier` 실제 발송 |
| Naver News API | Client ID/Secret | 네이버 개발자센터 | `NaverNewsAdapter`(SRC-0003, 현재 stub) |
| DART | API Key(무료) | OpenDART(opendart.fss.or.kr) | `DartFilingAdapter`(SRC-0004, 현재 stub) |
| KRX(KIND) | 없음(공개 웹사이트) — 구조화 API 존재 여부 TODO | — | SRC-0005(TODO) |
| SEC EDGAR | 없음 — User-Agent 헤더만 필요 | — | SRC-0006(TODO 구현) |
| EDINET | TODO: source required(API Key 필요 여부 미확인) | — | SRC-0007(TODO) |
| SEDAR+ | TODO: source required | — | SRC-0008(Pilot 대상 회사 없음) |
| Companies House | API Key(무료) | Companies House 개발자 계정 | SRC-0009(Pilot 대상 회사 없음) |

이 표는 `config/sources.yaml`의 `authentication` 필드(Round 6 TASK-K03)와 동일한 내용을
"무엇을 준비해야 하는가" 관점으로 재정리한 것이다 — 새 사실을 추가하지 않았다.

## 3. 환경변수 목록 (`.env.example` 기준, Round 7 갱신)

Round 7에서 그동안 누락되어 있던 `NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`,
`LCIP_TEST_EMAIL_RECIPIENT`, 모델 3종(`LCIP_CLASSIFICATION_MODEL`/
`LCIP_DEEP_ANALYSIS_MODEL`/`LCIP_FUTURE_READINESS_MODEL`)을 `.env.example`에 추가했다 —
이전까지는 코드(`claude_client.get_model_name()`, `notifiers.py`)가 참조하는 환경변수인데도
`.env.example`에 없어서, 실제로 무엇을 채워야 하는지 한눈에 알 수 없었다.

전체 목록은 `.env.example`을 그대로 참고한다(이 문서에 값을 복제하지 않는다 — 단일
진실 공급원 원칙, Round 6/7의 "중복 구조 제거" 지시와 동일한 이유).

## 4. OAuth 흐름 안내 (실행하지 않음, 안내만)

- **Google(Drive/Sheets/Gmail 공용)**: Desktop OAuth 또는 Service Account 중 선택
  (`docs/GOOGLE_DRIVE_SETUP.md`/`docs/GOOGLE_SHEETS_SETUP.md` 참고). 현재 `.env.example`은
  두 방식 모두의 자리를 마련해 두었다 — 어떤 방식을 쓸지는 사용자가 §24 질문 항목에서
  확정해야 한다.
- **Gmail 발신 계정**: Google과 별도로 Gmail API Scope(`gmail.send`) 동의가 필요하다.
- 이 Pilot은 OAuth 동의 화면을 자동으로 열거나 토큰을 발급받는 코드를 아직 실행하지
  않는다 — `GOOGLE_OAUTH_TOKEN_PATH`/`GMAIL_OAUTH_TOKEN_PATH`에 토큰 파일이 이미
  존재한다고 가정하는 지점까지만 구현되어 있다(TASK-005/006, dry-run).

## 5. Connection Test Plan (승인 후 실행 순서)

> **Round 12 갱신**: 아래 순서(RSS 우선)는 Round 7 시점의 권장안이었다. Architect
> Review Round 12가 `docs/RC2_CONNECTION_CHECKLIST.md` §2에서 새 우선순위(Claude API →
> Google Drive/Sheets → Google News RSS → DART → n8n API → Gmail → Telegram →
> Naver News)를 확정했다 — 실행 순서는 그 문서를 따른다. 아래 표의 "확인 방법" 칸은
> 여전히 유효하며 그대로 재사용한다.

**원칙: 위험(비용/외부 부작용)이 가장 낮은 연결부터, 하나씩, 매 단계 사이에 결과를
확인한다.** 아래 순서는 Round 7 시점 권장안이다(위 Round 12 갱신 참고).

| 단계 | 대상 | Feature Flag | 안전장치 | 확인 방법 |
|---|---|---|---|---|
| 1 | Google News RSS(SRC-0001) 1회 실호출 | `real_network_calls` | `GoogleRSSAdapter.enabled` 이중 게이트, 비용 없음(공개 RSS) | `scenarios/scenario_1_news_analysis.py`를 flag on 상태로 1회 실행, fixture 결과와 실제 파싱 결과 형태 비교 |
| 2 | Anthropic 분류 1건(`classification` tier, Haiku 계열) | `claude_api_enabled` | `ClaudeProvider.enabled` 이중 게이트, `cost_guard.py` 일일 상한 | 응답이 `relevance_output` 스키마를 통과하는지, `cost_tracking.py` 예상 비용이 목표($15)/상한($20) 이내인지 |
| 3 | Anthropic 심층분석 1건(`deep_analysis` tier, Sonnet 계열) | 위와 동일 | 위와 동일 + `daily_deep_analysis_limit`(일 5건) | `risk_analysis_output` 스키마 통과 여부 |
| 4 | Quick Company Scan 1건(`future` tier, Opus 계열) | 위와 동일 | 저빈도 고비용이므로 명시적 1회만 | `quick_company_scan.schema.json` Core 필드 통과 여부 |
| 5 | Gmail/Telegram 테스트 발송 1건 | `notification_send_enabled` | `test_mode=False` 전환 + 테스트 수신 계정 한정 | 실제 수신 확인, 발신 계정에 스팸/오발송 없는지 |
| 6 | Google Sheets 저장 1건 | `google_sheets_enabled` | `GoogleSheetsStorage.enabled` 이중 게이트 | ARTICLE_DB/INTELLIGENCE_DB 탭에 1행만 추가되는지, 기존 로컬 JSONL과 내용 일치 여부 |
| 7 | Naver/DART 어댑터 실구현 및 1회 호출 | `real_network_calls` | 현재는 stub(NotImplementedError) — 구현 자체가 선행 작업 | 구현 후 SRC-0001과 동일한 절차 |
| 8 | n8n 배포(TASK-008) | 해당 없음(n8n 자체 활성화) | 계획상 마지막 순서 | 수동 실행(Manual Trigger)으로 1회 확인 후 스케줄 활성화 |

각 단계 사이에는 반드시 `python3 scripts/quality_gate.py`를 재실행해 Mock Dependency가
의도한 만큼만 낮아졌는지 확인한다(의도치 않게 여러 Flag가 동시에 켜지지 않았는지 감시).

## 6. Rollback Plan

1. **즉시 중단(1순위)**: `config/feature_flags.yaml`에서 문제가 생긴 플래그를 다시
   `false`로 되돌린다. 코드 변경이 필요 없다 — 다음 실행부터 즉시 Mock/dry-run으로
   복귀한다. 이것이 이 아키텍처가 Round 6에서 설계된 이유다.
2. **Credential 회수**: 유출/오발급이 의심되면 해당 서비스 콘솔(Anthropic Console,
   Google Cloud Console, n8n, @BotFather 등)에서 즉시 Key/Token을 폐기하고
   재발급한다. `.env`는 Git에 포함되지 않으므로(`.gitignore`) 폐기 후 로컬 파일만
   교체하면 된다.
3. **실수로 발송된 알림**: `notification_send_enabled`를 즉시 `false`로 되돌리고,
   테스트 수신 계정에서 수동으로 확인·정리한다(자동 회수 기능 없음 — Pilot 범위 밖).
4. **저장된 잘못된 데이터**: `LocalJSONLStorage`/`GoogleSheetsStorage`에 잘못 쌓인
   레코드는 `intelligence_id`/`article_id`로 식별해 수동 삭제한다(자동 롤백 스크립트는
   Pilot 범위 밖 — Enterprise Backlog).
5. **비용 초과 조짐**: `cost_guard.py`의 90% 경고(`restrict_rate`)에서 긴급 건만 허용,
   100%(`hard_stop_rate`)에서는 `claude_api_enabled`를 즉시 `false`로 되돌린다.
6. 모든 롤백 조치 후 `python3 scripts/quality_gate.py`로 Mock Dependency가 원래
   수준(해당 플래그 기준 100%)으로 복귀했는지 재확인한다.

## 7. Architect 승인이 필요한 항목 (요약 — 상세는 Round 7 보고서 §55)

- 어떤 연결부터 시작할지(§5 순서 확정 또는 재조정)
- Google 인증 방식(Desktop OAuth vs Service Account) 최종 확정
- Naver/DART API Key 발급 여부 및 시점
- Claude 모델 ID 3종(Haiku/Sonnet/Opus 계열 정확한 버전) 확정
- 테스트 발송 수신 계정(이메일 주소, Telegram Chat ID) 지정
