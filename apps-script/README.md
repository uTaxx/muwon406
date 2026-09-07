# LX 회사 워크플로의 Apps Script 프로젝트

n8n에서 실행되던 회사(LX) 워크플로를 Google Apps Script로 옮기는 자리다.
설계는 `docs/앱스스크립트_이관_설계_2026-09-07.md`에 있다.
**지금은 기반만 있다. 어느 것도 실제 시스템에 연결돼 있지 않다.**

매매 쪽 Apps Script는 `uTaxx/sdlab_trading`의 `apps-script/trading`에 있다.
저장소를 나눈 뜻대로 회사 것은 여기, 매매 것은 저기다. 배포 워크플로는
같은 모양이고 비밀값 `CLASPRC_JSON`도 두 저장소에 각각 넣는다.

| 폴더 | 옮기는 것 | 지금 상태 |
|---|---|---|
| `lxgroup/` | 시간표 워크플로 10개(공시·원문·실적·비용·부문매핑·마스터정리·지표·운임·지표마스터·딜)와 조회 웹훅 4개(지표·경쟁사·딜·원본) | 웹 앱 입구, 식별코드 확인, 수집 작업 관리가 있다. 수집 단계와 조회는 자리만 있다. |

## 어떻게 올라가나

`.github/workflows/apps-script-deploy.yml`이 clasp로 올린다. `main`의
`apps-script/**`가 바뀌면 코드만 올리고(push), 사람이 `workflow_dispatch`로
`mode`를 골라 프로젝트를 새로 만들거나(create) 웹 앱 배포를 갱신한다(deploy).

`.clasp.json`의 `scriptId`가 비어 있으면 push는 빨갛게 끝난다. `create`로
만들고 로그에 찍힌 ID를 적어 커밋한다. `deployment.json`의 `deploymentId`도
같다. 처음 배포 때 로그에 찍힌 ID를 적어야 주소가 고정된다.

## 사람이 한 번 할 것

1. https://script.google.com/home/usersettings 에서 Google Apps Script API를 켠다. (2026-09-07에 켰다.)
2. PC에서 `npx @google/clasp login`을 실행한다. 생긴 `.clasprc.json`
   (윈도우 `C:\Users\<이름>\.clasprc.json`) 내용을 이 저장소의 GitHub 비밀값
   `CLASPRC_JSON`에 넣는다. 시트와 드라이브를 가진 구글 계정으로 로그인한다.
3. 첫 배포 뒤 https://script.google.com 에서 「LXGroup MI」 프로젝트를 열어
   `권한확인`을 실행하고 「허용」을 누른다.
4. 시트 `운영설정` 탭에 `TELEGRAM_BOT_TOKEN`과 `TELEGRAM_ADMIN_CHAT_ID` 줄을
   넣는다. API 키(DART, ECOS, FRED, 관세청, KOSIS)는 이미 그 탭에 있다.

## 시험

    cd apps-script && npm run check && npm test

Apps Script 파일은 전역을 같이 쓰는 스크립트라 `tests/gas.js`가 vm 문맥에
넣어 읽는다. 순수 함수만 시험한다. 시트·드라이브·바깥 호출을 쓰는 함수는
배포 뒤 편집기에서 `권한확인`으로 본다.

## 지키는 것

- 코드에 비밀값을 적지 않는다. 저장소가 공개다. 키는 시트 `운영설정`
  탭에서 읽는다. 시트에서 읽은 값을 `Logger.log`에 찍지 않는다.
- hub.html의 요청은 `text/plain`으로 와야 한다. HTTP 상태 코드를 못 정하므로
  거절은 본문 `ok:false`와 `상태` 칸에 적는다. 화면은 이미 `ok:false`를 본다.
