# GitHub Actions + 구글드라이브로 매일 자동매매 돌리기

PC를 계속 켜둘 필요 없이, 매일 장마감 후(15:30 KST) GitHub Actions가 자동으로
`scripts/run_paper_trading.py`를 실행한다. 보유 종목·가상현금 상태는
프로세스가 매번 새로 뜨는 GitHub Actions 특성상 로컬 디스크에 못 남기므로,
`muwon.db` 파일을 구글드라이브에 두고 실행 시작/종료마다 내려받고 올린다.

이 문서는 **사람이 웹 콘솔에서 직접 해야 하는 설정**을 순서대로 안내한다 —
코드는 이미 다 준비되어 있다 (`scripts/gdrive_sync.py`,
`.github/workflows/paper-trading.yml`).

## 1. 구글 클라우드 서비스 계정 만들기

서비스 계정은 "사람이 로그인하는 계정"이 아니라 "프로그램이 쓰는 전용 계정"이다.
GitHub Actions는 사람이 브라우저로 로그인할 수 없으니, 이게 필요하다.

1. https://console.cloud.google.com 접속 (구글 계정으로 로그인)
2. 상단 프로젝트 선택 드롭다운 → **새 프로젝트** → 이름 아무거나(예: `muwon406`) → 만들기
3. 만든 프로젝트가 선택된 상태에서, 좌측 상단 ☰ 메뉴 → **API 및 서비스** → **라이브러리**
4. 검색창에 `Google Drive API` 입력 → 클릭 → **사용** 버튼
5. 좌측 ☰ 메뉴 → **IAM 및 관리자** → **서비스 계정** → 상단 **+ 서비스 계정 만들기**
6. 이름 아무거나(예: `muwon406-bot`) 입력 → **만들고 계속하기** → 역할은 건너뛰어도 됨 → **완료**
7. 방금 만든 서비스 계정 클릭 → **키** 탭 → **키 추가** → **새 키 만들기** → **JSON** 선택 → 만들기
   → JSON 파일이 자동으로 다운로드된다. **이 파일을 잘 보관할 것** (나중에 GitHub Secrets에 붙여넣음)
8. 서비스 계정 이메일 주소를 복사해둘 것 — `xxx@muwon406.iam.gserviceaccount.com` 같은 형식
   (서비스 계정 목록 페이지에 표시됨)

## 2. 구글드라이브 폴더 만들고 공유

1. 구글드라이브(https://drive.google.com)에서 새 폴더 생성 (예: `muwon406-state`)
2. 그 폴더 우클릭 → **공유** → 위 7번에서 복사한 서비스 계정 이메일 주소 추가 → 권한 **편집자(Editor)** → 공유
3. 폴더를 열어서 주소창 URL을 본다: `https://drive.google.com/drive/folders/`**`이 뒤의 긴 문자열`**
   이 문자열이 "폴더 ID"다 — 복사해둘 것

## 3. GitHub Secrets 등록

`https://github.com/uTaxx/muwon406/settings/secrets/actions` 접속 →
**New repository secret**으로 아래 8개를 하나씩 추가.

| Secret 이름 | 값 |
|---|---|
| `MUWON_MASTER_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`로 새로 생성한 값 (기존에 쓰던 게 있으면 그걸로) |
| `KIS_APP_KEY` | KIS 모의투자 앱키 |
| `KIS_APP_SECRET` | KIS 모의투자 시크릿키 |
| `KIS_ACCOUNT_NO` | KIS 모의투자 계좌번호 (앞 8자리) |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇토큰 |
| `TELEGRAM_CHAT_ID` | 텔레그램 chat ID |
| `GDRIVE_SA_KEY_JSON` | 1번에서 다운로드한 JSON 키 파일을 **텍스트 에디터로 열어서 내용 전체**를 그대로 붙여넣기 |
| `GDRIVE_FOLDER_ID` | 2번에서 복사한 폴더 ID |

## 4. 첫 실행 확인

1. https://github.com/uTaxx/muwon406/actions/workflows/paper-trading.yml 접속
2. **Run workflow** 버튼 → 브랜치 확인 → **Run workflow**
3. 몇 분 뒤 실행 결과 확인 — 초록 체크면 성공. 빨간 X면 로그를 열어서 어느 단계에서 실패했는지 확인

첫 실행에선 구글드라이브에 `muwon.db`가 없어서 "새 상태로 시작합니다"라고 뜨는 게 정상이다.
그 다음부턴 매번 이어서 상태가 쌓인다.

## 5. 그 다음부턴

평일 15:30 KST(06:30 UTC)에 자동으로 돈다. 별도로 할 일 없음.

**리스크 정책(종목당 비중, 손절선, 자동매매 on/off 등)을 바꾸고 싶으면**:
지금은 대시보드가 로컬 `muwon.db`를 보게 되어 있어서, 구글드라이브에 있는
"진짜" 운영 상태를 직접 보려면 로컬로 내려받아야 한다.

```bash
python scripts/gdrive_sync.py download --folder-id <폴더ID> --filename muwon.db --out ./muwon.db
streamlit run src/muwon/dashboard/app.py   # 값 확인/수정
python scripts/gdrive_sync.py upload --folder-id <폴더ID> --filename muwon.db --path ./muwon.db
```

(`GDRIVE_SA_KEY_JSON`, `MUWON_MASTER_KEY`를 로컬 `.env`/환경변수에도 설정해야 함.)
매번 로컬↔드라이브를 오가야 하는 건 번거로운 부분이라, 나중에 대시보드가
구글드라이브를 직접 보게 만드는 것도 검토할 수 있다.

## 문제가 생기면

- **워크플로우가 KIS 접속 단계에서 실패**: `python scripts/configure.py kis ...`
  단계 로그에서 앱키/시크릿이 제대로 들어갔는지, `run_paper_trading.py` 로그에서
  KIS가 어떤 에러를 돌려줬는지 확인. GitHub Actions 러너에서 KIS 접속 자체는
  가능한 것으로 확인됨(모의투자 포트 29443 응답 확인됨).
- **구글드라이브 단계에서 실패**: 서비스 계정 이메일이 폴더에 편집자로 공유돼
  있는지, `GDRIVE_SA_KEY_JSON`에 JSON 전체가 (따옴표 손상 없이) 들어갔는지 확인.
