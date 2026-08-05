# Google Drive Setup — LCIP Pilot

TASK-005 산출물. `scripts/create_drive_structure.py`를 실제로 실행(`--apply`)하기 전에
아래 준비가 필요하다.

## 1. 인증 방식 선택 (사용자 결정 필요 — §24 질문 #1)

셋 중 하나를 고른다.

1. **Google OAuth Desktop App** — 개인 Google 계정으로 직접 인증. 별도 GCP 프로젝트에서
   OAuth Client ID(Desktop App 유형) 발급 필요.
2. **Service Account** — GCP 서비스 계정 생성 후, Drive에서 대상 폴더를 서비스 계정 이메일에
   "편집자"로 공유. 자동화에 적합하나 최초 GCP 설정이 더 필요하다.
3. **n8n Google Drive Credential만 사용** — 로컬 스크립트는 폴더 생성 "계획"만 만들고, 실제
   생성은 n8n의 Google Drive 노드(사용자가 n8n UI에서 직접 OAuth 연결)로 수행한다. 로컬 Python
   의존성이 가장 적다.

이번 라운드(TASK-001~007)에서는 기본값을 3번(n8n_only)으로 두었다 — 로컬에서 실제 Google API를
전혀 호출하지 않는다.

## 2. 기존 Root Folder 존재 여부 확인 (§24 질문 #2)

이미 만들어둔 `LCIP_PILOT` Drive 폴더가 있다면 해당 폴더 ID를 `.env`의
`GOOGLE_DRIVE_ROOT_FOLDER_ID`에 넣어야 한다. 없다면 최초 생성이 필요하다 — 이 값은
`create_drive_structure.py`가 dry-run 출력에서 알려준다.

## 3. dry-run 실행

```bash
cd LCIP_PILOT
python scripts/create_drive_structure.py --dry-run
```

`config/drive_structure.yaml`에 정의된 폴더 계획만 출력하며 어떤 외부 API도 호출하지 않는다.

## 4. 실제 생성 (사용자 승인 후에만)

```bash
export LCIP_CONFIRM_APPLY=yes   # 명시적 승인의 증거
python scripts/create_drive_structure.py --apply --auth-mode <oauth_desktop|service_account|n8n_only>
```

`n8n_only` 모드에서는 이 명령도 실제로 아무것도 쓰지 않고, 계획을 n8n 워크플로우에서
수동/노드 기반으로 반영하라는 안내만 출력한다. `oauth_desktop`/`service_account` 모드의
실제 쓰기 로직은 TASK-008(외부 연결 승인) 라운드에서 사용자 승인 후 완성한다.

## 5. 생성될 폴더 구조

`config/drive_structure.yaml` 참고 (`03_BUILD_SPECIFICATION.md` TASK-005 기준):

```text
LCIP_PILOT/
├─ 00_Project/
├─ 01_Knowledge/
├─ 02_Data/
├─ 03_Dashboard/
├─ 04_Reports/
│  └─ CURRENT/
├─ 05_Archive/
└─ 06_Admin/
```
