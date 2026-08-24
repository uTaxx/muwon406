# 주식 시스템을 sondul-trading으로 옮긴다 (2026-08-24)

## 왜 옮기나

지금 이 시스템은 **남의 저장소에 곁방살이 중**이다.

```
uTaxx/muwon406
  ├─ main                  ← 맛집·카페 대시보드 (Pages 자리를 쓰고 있다)
  └─ claude/reset-lfe6ro   ← 주식매매 시스템 (여기)
```

상관없는 두 프로젝트가 브랜치로 나뉘어 한 저장소에 들어 있다. 그래서
셋이 막혀 있다.

| 막힌 것 | 이유 |
|---|---|
| `main`을 못 쓴다 | 맛집 대시보드가 쓰고 있다 |
| Pages에 화면을 못 올린다 | **Pages는 저장소당 하나**고, 그 자리도 맛집이 쓴다 |
| 브랜치 이름이 `claude/reset-lfe6ro` | 자동 생성된 이름이 그대로 굳었다 |

저장소를 나누면 셋이 한 번에 풀린다. 이름은 **`uTaxx/sondul-trading`**,
브랜치는 **`main`**이다.

---

## 무엇이 가고 무엇이 남나

**전부 간다.** 파이썬 코드, 워크플로 19개, 문서, 테스트, 커밋 177개까지.
`claude/reset-lfe6ro`에 있는 것이 그대로 새 저장소의 `main`이 된다.

**남는 것**: `muwon406`의 `main`(맛집 대시보드)은 손대지 않는다. 그쪽
Pages 배포도 그대로 돈다.

---

## 순서 — 끊기는 시간 없이

옛 저장소를 **계속 살려 둔 채로** 새 쪽을 세우고, 다 되면 n8n만 옮긴다.
그래서 중간에 매매가 멈추는 구간이 없다.

### 1단계 · 사람 — 빈 저장소 만들기

github.com → **New repository**

| 칸 | 값 |
|---|---|
| Repository name | `sondul-trading` |
| 공개 여부 | **Public** (Pages를 무료로 쓰려면 공개여야 한다) |
| Add a README | **체크 해제** |
| .gitignore / license | **None** |

> README를 체크하면 빈 저장소가 아니게 되어 기존 커밋 177개를 밀어 넣을 때
> 충돌한다. 반드시 비워 둔 채로 만든다.

**왜 사람이 하나**: GitHub 연동이 저장소 만들기 권한을 안 준다(403).
이 한 단계만 사람 손이 필요하다.

### 2단계 · 내가 — 코드 밀어 넣기

```
git push sondul claude/reset-lfe6ro:main
```

커밋 177개가 이력째로 간다. **복사가 아니라 이동이라 "언제 왜 이렇게
됐는지"가 새 저장소에서도 그대로 보인다.**

### 3단계 · 사람 — 비밀값 8개 넣기

새 저장소 → **Settings → Secrets and variables → Actions → New repository secret**

값은 **지금 muwon406에 들어 있는 것과 똑같다.** 다만 GitHub이 저장된 비밀값을
다시 보여 주지 않으므로, 원본을 어디서 받아 왔는지를 기준으로 다시 넣어야 한다.

| 이름 | 무엇 |
|---|---|
| `KIS_APP_KEY` | 한국투자증권 앱키 |
| `KIS_APP_SECRET` | 한국투자증권 앱시크릿 |
| `KIS_ACCOUNT_NO` | 계좌번호 앞 8자리 |
| `TELEGRAM_BOT_TOKEN` | 무원406 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 알림 받을 채팅 ID |
| `GDRIVE_SA_KEY_JSON` | 구글 드라이브 서비스계정 키(JSON 통째로) |
| `GDRIVE_FOLDER_ID` | 장부(`muwon.db`)가 든 폴더 ID |
| `MUWON_MASTER_KEY` | 저장된 자격증명을 푸는 열쇠 |

**왜 사람이 하나**: 비밀값은 내가 만들 수도, 읽을 수도 없다. GitHub API도
기존 값을 안 돌려준다.

### 4단계 · 사람 — n8n이 쓸 GitHub 열쇠에 새 저장소 붙이기

지금 PAT(개인 접근 토큰)는 `muwon406` **하나만** 가리키게 만들어져 있다.

github.com → **Settings → Developer settings → Personal access tokens →
Fine-grained tokens** → 쓰던 토큰 → **Repository access**에 `sondul-trading`
추가. 권한은 **Actions: Read and write** 하나면 된다.

> 새로 만들지 말고 **기존 토큰에 저장소를 추가**하는 편이 낫다. 새로 만들면
> n8n 자격증명도 같이 바꿔야 한다.

### 5단계 · 내가 — 새 저장소에서 검증

워크플로를 손으로 한 번씩 돌려 본다. 여기서 걸리면 아직 n8n은 옛 저장소를
보고 있으므로 **매매에는 영향이 없다.**

### 6단계 · 사람 — n8n 주소 갈아 끼우기 (일곱 곳)

이관에서 **유일하게 위험한 단계**다. 여기를 바꾸는 순간 매매가 새 저장소를
본다. 5단계가 통과한 뒤에 한다.

**⚠️ 브랜치는 리다이렉트가 없다.** 저장소 이름은 GitHub이 옛 이름을
새 이름으로 넘겨 주지만, 브랜치는 안 넘겨 준다. `ref`를 안 고치면
그 자리에서 422로 실패한다.

#### `AutoTrading_계좌조회` — 1곳

「저장소에서 화면 가져오기」 노드의 URL

```
바꾸기 전  https://raw.githubusercontent.com/uTaxx/muwon406/claude/reset-lfe6ro/site/index.html
바꾼 뒤    https://raw.githubusercontent.com/uTaxx/sondul-trading/main/site/index.html
```

#### `AutoTrading_Schedule` — 5곳

다섯 노드 전부. URL의 `uTaxx/muwon406` → `uTaxx/sondul-trading`,
본문(JSON)의 `"ref"` → `"main"`.

| 노드 | 워크플로 파일 |
|---|---|
| 시장·섹터 리포트 부르기 | `market-report.yml` |
| 매수 후보 제안 부르기 | `propose-buys.yml` |
| 승인된 것만 매수 부르기 | `execute-approved.yml` |
| 30분봉 수집 부르기 | `collect-intraday.yml` |
| 기록을 시트로 부르기 | `push-records.yml` |

```
바꾸기 전  https://api.github.com/repos/uTaxx/muwon406/actions/workflows/<파일>/dispatches
           { "ref": "claude/reset-lfe6ro", ... }

바꾼 뒤    https://api.github.com/repos/uTaxx/sondul-trading/actions/workflows/<파일>/dispatches
           { "ref": "main", ... }
```

#### `AutoTrading_Telegram` — 1곳

「깃허브로 넘기기」 노드. 위와 같은 모양(`telegram-n8n.yml`).

**세 워크플로 전부 `Publish`를 눌러야 반영된다.**

> **왜 사람이 하나**: 이 세션에서 n8n을 *바꾸는* 도구 호출이 자동 승인
> 심사에 막힌다. 읽기와 실행은 되므로, 바꾼 뒤 제대로 됐는지는 내가 읽어서
> 확인할 수 있다.

### 7단계 · 사람 — 스트림릿 옮기기 (급하지 않다)

share.streamlit.io → 앱 설정 → Repository를 `uTaxx/sondul-trading`,
Branch를 `main`으로.

**2주 병행하기로 했으므로 서둘 것 없다.** 새 대시보드가 자리를 잡으면
그때 스트림릿은 지운다.

---

## 되돌리는 법

6단계까지 갔다가 문제가 생기면, **n8n의 일곱 곳을 옛 주소로 되돌리면
끝난다.** 옛 저장소와 브랜치를 지우지 않고 두는 이유가 이것이다.

새 저장소를 지울 필요도 없다 — n8n이 안 부르면 아무 일도 안 한다.

옛 저장소는 **새 쪽에서 매매가 며칠 정상으로 돈 뒤에** 정리한다.

---

## 이관이 끝나면 남는 그림

```
uTaxx/sondul-trading  (공개)
  └─ main
      ├─ 파이썬 — 판단·주문. 안전장치가 여기 있다
      ├─ .github/workflows — 19개
      └─ 대시보드 — Pages 자리가 비어 있다 ★
```

★ 이 자리가 이번 이관의 진짜 이유다. 여기에 화면 하나를 올려 스트림릿·
시트·n8n 화면으로 흩어져 있던 관리 지점을 하나로 모은다.

관리 지점: **다섯 → 둘**(화면 하나 + 텔레그램 알림).
