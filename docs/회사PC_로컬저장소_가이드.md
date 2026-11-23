# 회사 PC 로컬 저장소 가이드

GitHub 없이 회사 PC 한 대에서 이 저장소를 받아 작업하고 백업하는 방법이다. 클라우드 세션에서 만든 저장소를 `muwon406.bundle` 파일 하나로 옮긴다. 이 파일에는 커밋 이력이 모두 들어 있다.

## 1. 준비

- 회사 PC에 Git이 설치되어 있어야 한다. PowerShell 또는 터미널에서 `git --version`을 실행해 확인한다.
- `muwon406.bundle` 파일을 회사 PC로 옮긴다(메일, 사내 공유 폴더, USB 등 회사 정책에 맞는 방법).
- 작업 폴더를 정한다. 예: `C:\work`. 사용자 폴더 아래의 OneDrive 동기화 폴더는 피한다. 동기화가 `.git` 폴더를 깨뜨리는 일이 있다.

## 2. 저장소 가져오기

PowerShell에서 실행한다.

```powershell
cd C:\work
git clone muwon406.bundle muwon406
cd muwon406
git branch -m main
git remote remove origin
git config user.name "이름"
git config user.email "회사 메일 주소"
git log --oneline -5
```

- `git clone`은 bundle 파일을 원격 저장소처럼 읽는다. 복제 직후 `origin`이 bundle 파일 경로를 가리키므로 `git remote remove origin`으로 지운다.
- `git branch -m main`은 작업 브랜치 이름을 `main`으로 바꾼다.
- `git log` 첫 줄이 「시스템 설명 txt 추가」 또는 이후 커밋이면 정상이다.

macOS·리눅스에서는 `cd`의 경로만 바꾸고 나머지는 같다.

## 3. 일상 작업

작업 단위가 끝날 때마다 커밋한다.

```powershell
git status
git add -A
git commit -m "무엇을 왜 바꿨는지 한 줄"
```

- `.env`, 데이터베이스 파일, 로그, `node_modules`는 `.gitignore`에 들어 있어 커밋되지 않는다.
- API 키와 비밀번호는 어떤 파일에도 적어서 커밋하지 않는다. 서버 설정 파일(`server/.env`)에만 둔다.

## 4. 백업

로컬 저장소는 PC 한 대에만 있으므로 PC가 고장 나면 이력이 사라진다. 정기적으로 bundle 파일로 백업한다.

```powershell
# 저장소 폴더에서 실행. 기본 저장 위치는 사용자 폴더의 Backups\muwon406
.\scripts\backup_bundle.ps1
# 사내 네트워크 드라이브로 보낼 때
.\scripts\backup_bundle.ps1 -Dest "\\서버\공유\muwon406"
```

- 스크립트는 `muwon406-날짜-시각.bundle` 파일을 만들고 검증까지 한다. 오래된 백업은 자동으로 지우지 않으므로 필요하면 수동으로 정리한다.
- 주 1회 이상, 큰 작업이 끝날 때마다 실행하는 것을 권한다. Windows 작업 스케줄러에 등록해도 된다.
- 복구는 백업 파일로 2번과 같은 방식으로 다시 `git clone` 하면 된다.

macOS·리눅스는 `scripts/backup_bundle.sh`를 쓴다.

## 5. Claude Code로 이어서 작업하기

회사 PC에 Claude Code를 설치할 수 있는지는 IT 보안 정책을 확인해야 한다. 허용되면 저장소 폴더에서 실행하고 첫 지시를 다음처럼 준다.

```
docs/시스템_설명.txt, CLAUDE.md, docs/HANDOVER.md, server/README.md 를 읽고
이 시스템을 회사 서버 프로그램으로 옮기는 작업의 현재 상태를 요약해 줘.
요약이 맞으면 server/README.md 의 1단계(뉴스 MI)부터 시작하자.
```

## 6. 옮기기 전에 정리할 것

이 저장소는 지금까지 공개 저장소였으므로 사내 정보가 일부 들어 있다. 점검한 결과는 다음과 같다(값은 문서에 적지 않았다).

| 항목 | 위치 | 조치 |
|---|---|---|
| 구글 API 키 1건 | `public/lxgroup-mi/hub.html`의 `ARTICLES_STATIC_API_KEY` | 회사 구성에서 구글 드라이브 공개 파일을 쓰지 않으면 삭제. 쓰면 회사 계정에서 새 키를 발급 |
| 이메일 주소 | `hub.html` 2건, 이관 계획 문서 1건 | 개인·사내 주소이므로 필요 없으면 삭제 |
| n8n 주소 | `hub.html` 29곳 | 서버 프로그램으로 옮길 때 새 주소로 교체 |
| 기존 GitHub 저장소 | `utaxx/muwon406` | 이관이 끝나면 비공개로 전환하거나 삭제할지 결정 |

이관이 끝난 뒤에는 `CLAUDE.md` 첫 부분의 「이 저장소는 공개(public)다」 문구를 실제 상태에 맞게 고친다. 키·비밀번호·토큰을 파일에 넣지 않는 규칙은 로컬 저장소에서도 유지한다.

## 7. 이 bundle에 들어 있지 않은 것

- 다른 `claude/*` 브랜치(LCIP 파일럿, Apps Script 원본 등). 필요하면 GitHub에서 따로 받는다.
- n8n 워크플로우 정의. n8n 서버에만 있다. 서버 프로그램으로 옮기는 작업에서 로직을 코드로 옮긴다.
- 구글 시트의 데이터(키워드, 설정, 피드백, 경쟁사 목록). 시트를 내보내서 가져와야 한다.
