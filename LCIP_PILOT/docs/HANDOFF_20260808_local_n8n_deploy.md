# 인수인계서 — 로컬 세션 n8n 실제 배포 (2026-08-08)

> 이 문서는 **로컬 Claude Code 세션(사용자 PC, `E:\lcip` 클론)**에서 수행한 작업을
> 정리한 것이다. 이후 작업은 **클라우드 Claude Code(claude.ai/code, uTaxx 계정,
> `muwon406` 저장소 `claude/lx-corporate-intelligence-f2ocw2` 브랜치 채팅방)**에서
> 이어간다. 클라우드 세션은 이 브랜치를 `git pull`하면 아래 변경사항을 그대로 받는다.

## 0. 이 세션이 어떤 환경이었나 (혼동 방지)

- **로컬 Claude Code** (사용자 PC, Windows, 모델 Opus). gh CLI/브라우저 모두
  **`sondullab` 계정**으로 로그인돼 있었다.
- 저장소 `uTaxx/muwon406`은 **`uTaxx` 계정 소유**다. 클라우드 세션은 uTaxx로 붙어
  있었으나, 사용자가 권한 이슈로 로컬 새 창(sondullab)으로 옮겨와 이 작업을 했다.
- 로컬 클론 위치: **`E:\lcip`** (원격 origin = `https://github.com/uTaxx/muwon406.git`,
  브랜치 `claude/lx-corporate-intelligence-f2ocw2`). 프로젝트 루트는 `E:\lcip\LCIP_PILOT`.
- ⚠️ 로컬엔 별개 저장소 `E:\Sondullab`(=`Sondullab/sondullab`, 손덜Lab용)도 있다 —
  **LCIP와 무관**하니 섞지 말 것.

## 1. ✅ 완료: n8n 워크플로우 5개 실제 배포

사용자 지시 "N8N 재배포"에 따라 `scripts/n8n_deploy.py --apply`를 **실제 n8n Cloud에
최초로 실행**했다.

- **대상 인스턴스**: `https://sondullab.app.n8n.cloud`
  — 손덜Lab/LXGroup 워크플로우가 이미 운영 중인 그 인스턴스와 **동일**(사용자 확인).
  즉 LCIP의 `N8N_BASE_URL`이 이 값으로 확정됐다(그동안 미확보 Blocker였음).
- **인증**: `N8N_API_KEY` 사용(손덜Lab/LXGroup에서 쓰던 그 n8n API 키와 동일 값).
  값 자체는 저장소에 없음(.gitignore) — 로컬 `E:\Sondullab\.claude\settings.local.json`에
  등록돼 있고, 클라우드에선 "Activate" 탭에서 제공된 그 값과 같다.
- **결과**: 5개 전부 신규 생성(POST), 전부 `active:false`. 기존 운영 워크플로우
  (LXGroup_* 4개, Sondullab_* 6개)는 삭제·변경 없이 그대로.

| 워크플로우 이름 | n8n workflow id | 상태 |
|---|---|---|
| LCIP - Master Pipeline (WF-P01) | `pIBUQlxurc8EVOa0` | active:false |
| LCIP - Source Health (WF-P08) | `SakyzFgM9d8FUN1R` | active:false |
| LCIP - Cost Guard (WF-P09) | `irZ4sPGuNq1HKatH` | active:false |
| LCIP - Natural Language Admin (WF-P10) | `QPjThtVINHyuCC9o` | active:false |
| LCIP - Error Handler (WF-P99) | `9O5cvmcs5Qs0W6RV` | active:false |

- **해소된 리스크**: `n8n_deploy.py` 주석에 있던 "실제 n8n 인스턴스로 미검증,
  `name`/`nodes`/`connections`/`settings` 페이로드 계약 미확인"이 이번 실행으로
  검증됐다 — 그 계약 그대로 정상 동작(400 없음).

### 재실행/재현 방법 (다음에 또 배포할 때)

`E:\lcip\LCIP_PILOT`에서:
```bash
export N8N_BASE_URL='https://sondullab.app.n8n.cloud'
export N8N_API_KEY='<손덜Lab n8n API 키>'
export LCIP_CONFIRM_APPLY=yes
python scripts/n8n_deploy.py --apply
```
- 의존성: `pyyaml`(_common.py가 import), `requests`(설치돼 있음). Python 3.14에서 동작.
- 이름 매칭이라 **재실행해도 중복 생성 안 됨**(이미 있으면 PUT 갱신). 삭제는 절대 안 함.
- 인증/네트워크 없이 계획만 보려면 `--apply` 빼고 실행(dry-run).

## 2. ✅ 완료: GitHub push 권한 문제 해결

- **문제**: 로컬이 sondullab 계정인데 저장소는 uTaxx 소유라 sondullab의 push 권한이
  없었다(clone/읽기만 가능, push 불가).
- **해결(사용자가 방법 A 선택)**: 저장소는 uTaxx 소유 그대로 두고, uTaxx가
  **sondullab을 협업자(Write)로 초대** → sondullab 쪽에서 초대 수락 완료.
  이제 로컬 `E:\lcip`에서 sondullab 계정으로 uTaxx/muwon406에 바로 push 가능.
- 이 인수인계서와 아래 문서 갱신도 그 권한으로 push된다.

## 3. ✅ 완료: 프로젝트 문서 갱신

이번 커밋에 포함(코드 변경 없음, 기록만):
- `PROJECT_STATUS.md` — 최상단에 "n8n 실제 배포 실행 (2026-08-08)" 절 추가(위 표/ID 포함),
  "최종 갱신" 라인 갱신.
- `CHANGELOG.md` — `[Unreleased]`에 "Deployed — n8n 워크플로우 5개 실제 배포" 항목 추가.
- `docs/HANDOFF_20260808_local_n8n_deploy.md` — 이 파일.

## 4. ⏭ 아직 안 된 것 / 다음 단계 (클라우드 세션에서 이어갈 것)

배포는 됐지만 **아직 실제로 돌지 않는다**. 활성화까지 남은 것:

1. **n8n Credential 연결 + 활성화** — 배포된 5개는 비활성 + Credential 미연결이다.
   n8n UI에서 각 워크플로우에 Google Sheets/Telegram/Anthropic Credential을 붙이고
   WF-P01을 활성화해야 실제 뉴스 수집이 시작된다. (WF-P01 내부 노드가 정확히 어떤
   Credential/시트/키를 참조하는지 먼저 점검 필요 — 아직 이 세션에서 열어보지 않았다.)
2. **Google Sheets 연동** — 클라우드 세션 재시작 계획의 나머지 2단계:
   - `.env` 재생성: Anthropic/Google OAuth/n8n/Telegram/DART/Naver 6개 항목.
     **실제 값은 이 로컬엔 없다** — 클라우드 대화(+ Google Drive Sheet "Activate" 탭)에
     있다. 클라우드 세션에서 이어가면 그 값 그대로 쓸 수 있다.
   - `credentials/token.json` 재생성: `scripts/local_oauth_setup.py`를 **사용자 PC에서
     1회 실행**(브라우저 승인) → 생성된 token.json 내용을 Claude에게 붙여넣기.
     (클라우드 샌드박스엔 브라우저/localhost가 없어서 못 하고, 로컬 PC에서 해야 함.)
   - `GOOGLE_SHEETS_MASTER_SPREADSHEET_ID` 미확보 — Master Spreadsheet 자동 생성 코드는
     있음(`scripts/create_google_sheets.py --apply`).
3. **DART/Naver 어댑터** — 아직 stub(회사명→corp_code 매핑 등 추가 설계 필요).
4. **Priority 1 결정 대기**: `feature_flags.yaml`의 `claude_api_enabled`를 상시 켤지
   (Scenario가 상시 실제 비용 발생) — 실제 비용 결정이라 자동 진행 대상 아님.

## 5. 현재 상태 스냅샷

- **브랜치/커밋**: `claude/lx-corporate-intelligence-f2ocw2`. 이 인수인계 커밋 직전 HEAD는
  `fff4880`("Service Account 키 생성 조직 정책 차단 대응 — 로컬 OAuth 1회 승인 스크립트 추가").
- **n8n 인스턴스**(`sondullab.app.n8n.cloud`) 워크플로우 총 17개 = LCIP 신규 5개(전부 off)
  + LXGroup_* 4개(운영) + Sondullab_* 6개(운영) + 기존 비활성 2개(LXGroup_Setting, test_lx).
- **테스트**: 이 세션에선 코드 변경이 없어 재실행 안 함(직전 상태 487개 PASS 유지).
