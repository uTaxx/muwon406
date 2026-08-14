# 맛집·카페 검색 대시보드

키워드/지역으로 맛집·카페를 검색하고, 지도에서 위치를 확인하고, 평점·리뷰순으로 정렬하고, 즐겨찾기(찜)할 수 있는 대시보드입니다.

## 디자인

민트 톤 primary 컬러 + 웜톤 오프화이트 배경, 큰 라운드 코너와 소프트 elevation을 쓰는 파스텔 스타일가이드를 기준으로
꾸몄습니다. 색상 팔레트는 `tailwind.config.js`의 `brand` 스케일에, 카드/버튼 radius는 `rounded-card`/`shadow-soft`/
`shadow-elevated` 커스텀 토큰에 정의되어 있습니다. 한글 가독성이 좋은 [Pretendard](https://github.com/orioncactus/pretendard)를
기본 폰트로 CDN에서 불러와 사용합니다 (`index.html`).

## 주요 기능

- 키워드/지역 검색 (가게명, 메뉴, 태그, 지역명, 주소)
- 음식 종류별 세부 카테고리 필터 (숯불구이, 철판구이, 한식, 디저트카페 등)
- 평점순 / 리뷰 많은순 / 거리순 / 가격 낮은순 정렬
- 즐겨찾기(찜) — 브라우저 localStorage에 저장되어 새로고침해도 유지
- 카카오맵 연동 (API 키 설정 시 실제 지도에 마커 표시)
- 체험단/협찬 리뷰 이벤트 진행 중인 곳 제외 필터
- 광고성 리뷰 비율이 높은(40% 이상) 곳 제외 필터
- 가게 카드를 클릭하면 리뷰 N개(5/10/20/30/50개, 조정 가능·기본 20개)를 분석해 광고성/일반 리뷰로 구분해서 보여줌
- 업력(개업 연도 기준 운영 연차) 표시
- 사업자등록일과 개업 연도를 비교해 "주인이 바뀌었을 가능성"을 추정 표시 (실제 이력 조회 아님, 아래 설명 참고)
- 회식용 룸 보유 여부 및 최대 인원 표시, "룸 있는 곳만 보기" 필터

### 리뷰 품질 필터 & 리뷰 분석에 대해

`Restaurant` 데이터에는 `hasReviewEvent`(체험단/협찬 진행 여부)와 `sponsoredReviewRatio`(광고성 리뷰 추정 비율, 0~100)
필드가 있습니다. 지금은 샘플 데이터에 값이 채워져 있어 필터가 바로 동작하지만, 실제 값은 블로그 리뷰 본문을 수집해
광고/협찬 표기나 문체를 분석하는 별도 파이프라인이 있어야 채울 수 있습니다. 카카오/네이버/구글 provider는 아직
이 신호를 제공하지 않아 기본값(`false`, `0`)으로 채워집니다 — 실제 서비스에서 이 필터를 쓰려면 리뷰 크롤링·분류
로직을 추가해 이 두 필드를 채워주세요.

가게 카드를 펼치면 나오는 "리뷰 N개 분석 결과"는 아직 실제 블로그 리뷰를 가져오는 연동이 없어서, 데모용으로
리뷰를 생성한 뒤 `src/utils/reviewClassifier.ts`의 문구 패턴(예: "협찬", "체험단", "제공받아", "원고료")으로
광고성 여부를 분류합니다. 이 패턴은 실제 표시광고법상 고지 문구를 참고해 만들었으므로, 실제 리뷰 수집 파이프라인이
생기면 `src/utils/generateReviews.ts`를 실제 API 호출로 교체하고 `reviewClassifier.ts`의 분류 로직은 그대로
재사용하면 됩니다.

### 사업자 조회/주인 변경 추정에 대해

국세청 "사업자등록정보 진위확인 및 상태조회" API(공공데이터포털에서 무료 신청 가능)를 쓰면 사업자등록번호의
**현재 상태**(계속사업자/휴업자/폐업자)와 **등록일자**는 조회할 수 있습니다. 하지만 "이전 사업자가 언제 폐업하고
새 사업자가 언제 등록했는지"에 대한 이력은 개인정보·영업비밀 보호 때문에 공개 API로 제공되지 않습니다.

그래서 이 대시보드는 **개업 연도**(`openedYear`)와 **사업자등록일**(`businessRegistrationDate`)을 비교해서,
등록일이 개업 연도보다 2년 이상 늦으면 "중간에 주인이 바뀌었을 가능성"으로 추정 표시합니다
(`src/utils/businessInfo.ts`의 `estimateOwnerChange`). 실제 소유권 변경 이력이 아니라 정황상 추정치이므로
UI에도 항상 "실제 이력이 아닌 추정치"라고 명시합니다. 카카오/네이버/구글 provider는 이 정보를 제공하지 않아
`openedYear`/`businessRegistrationDate`가 비어 있으면 관련 UI가 자동으로 숨겨집니다.

## 시작하기

```bash
npm install
npm run dev
```

기본값은 **샘플(mock) 데이터**로 동작하므로 별도 API 키 없이 바로 실행할 수 있습니다.

## 실제 데이터 연동하기

1. `.env.example`을 `.env`로 복사합니다.
2. `VITE_DATA_SOURCE`를 `kakao`, `naver`, `google` 중 하나로 바꿉니다. (기본값 `mock`)
3. 아래 표를 참고해 필요한 키를 채워 넣습니다.

| 소스 | 필요한 값 | 브라우저에서 바로 호출 가능? |
| --- | --- | --- |
| 카카오맵(지도 표시) | `VITE_KAKAO_MAP_KEY` (JS 키) | 예 |
| 카카오 로컬 검색 | `VITE_KAKAO_REST_API_KEY` (REST API 키) | 예 (`src/services/providers/kakaoProvider.ts`) |
| 네이버 검색 | `VITE_NAVER_CLIENT_ID` / `VITE_NAVER_CLIENT_SECRET` | 아니오 — 서버 프록시 필요 |
| 구글 플레이스 | `VITE_GOOGLE_PLACES_KEY` | 권장하지 않음 — 서버 프록시 필요 |

네이버와 구글은 브라우저에서 직접 호출하면 CORS 차단 또는 키 노출 문제가 있어 프록시가 필요합니다. `src/services/providers/naverProvider.ts`, `googleProvider.ts` 안에 프록시 구성 방법이 주석으로 설명되어 있습니다. 서버(예: Vercel Serverless Function, Express 등)를 준비한 뒤 두 provider의 요청 대상을 그 엔드포인트로 바꾸면 됩니다.

카카오 지도와 로컬 검색은 REST API 키만으로 브라우저에서 바로 호출할 수 있어 우선 연동해보기 좋습니다.

업력/사업자 상태를 실제 값으로 채우려면 공공데이터포털(data.go.kr)에서 "국세청_사업자등록정보 진위확인 및
상태조회 서비스"를 신청해 서비스 키를 발급받아야 합니다. 이 API도 브라우저에서 직접 호출하도록 공식 지원되지
않아 서버 프록시가 필요합니다.

## 실시간 검색 + 누적 저장 파이프라인 (n8n + Google Sheets)

`VITE_DATA_SOURCE=live`로 설정하면 대시보드가 정적 파일이 아니라 n8n 웹훅을 실시간으로 호출합니다.

```
대시보드에서 검색 (키워드/지역 있음)
  → n8n 웹훅(GET) 호출
  → 카카오 로컬 API 실시간 검색
  → Google Sheets("restaurants" 탭)에서 같은 id의 기존 데이터를 읽어 회식룸/업력/사업자정보 등
    수동 필드를 유지한 채 병합
  → 병합 결과를 시트에 upsert(카카오 id 기준)로 반영 — 검색될 때마다 데이터베이스가 누적됨
  → 병합 결과를 대시보드에 바로 응답

대시보드를 검색어 없이 처음 열 때
  → 같은 웹훅을 파라미터 없이 호출 → 지금까지 시트에 쌓인 전체 목록을 그대로 반환 (기본 화면용)
```

즉 정해진 지역을 매일 도는 배치 크롤링이 아니라, **사람들이 실제로 검색한 곳만 데이터베이스에 쌓이는 구조**입니다. 카테고리 필터·정렬처럼 이미 받아온 데이터로 처리 가능한 조건은 프론트엔드(`filterAndSortRestaurants`)에서 처리하고, 키워드/지역이 바뀔 때만 웹훅을 다시 호출합니다 (`src/App.tsx`).

**n8n**: `맛집·카페 실시간 검색 + 누적 저장` 워크플로우가 Active 상태로 배포되어 있고, 웹훅 URL은 `.env.example`의 `VITE_N8N_SEARCH_WEBHOOK_URL`에 있습니다. 카카오 REST API Key(Header Auth)와 Google Sheets OAuth 자격증명이 이미 연결되어 있습니다.

**Google Sheets**: 스프레드시트 안에 `restaurants` 탭이 실데이터베이스 역할을 합니다. 카카오 로컬 API가 주지 않는 값(회식룸 여부, 업력, 사업자등록일 등)은 이 시트에서 `id`(카카오 장소 id)로 해당 행을 찾아 직접 입력하면, 다음 검색/조회 때 자동으로 반영됩니다. 사업자등록번호와 개업 연도는 어떤 API도 주지 않는 정보라 사람이 직접 조사해서 채워야 합니다.

**GitHub / GitHub Pages**: 이 저장소는 이제 코드(앱)만 호스팅합니다. `.github/workflows/deploy.yml`이 `main` push마다 Vite 빌드 후 GitHub Pages에 배포합니다 (Settings → Pages → Source를 "GitHub Actions"로 설정). 데이터는 더 이상 저장소에 커밋되지 않습니다.

## 프로젝트 구조

```
src/
  types/restaurant.ts        # 맛집/카페 데이터 타입 정의
  data/mockRestaurants.ts    # 샘플 데이터 (실제 API 응답과 동일한 필드 구조)
  utils/filterRestaurants.ts # 키워드/지역/카테고리 필터 + 정렬 로직
  services/providers/        # 데이터 소스 추상화 (mock/live/kakao/naver/google)
  hooks/                     # 즐겨찾기(localStorage), 카카오맵 SDK 로더
  components/                # 검색바, 필터, 정렬, 카드, 지도, 즐겨찾기 패널
  App.tsx                    # 전체 레이아웃 및 상태 관리 (키워드/지역 변경 시에만 provider 재호출)
.github/workflows/deploy.yml # GitHub Pages 자동 배포 (코드만, 데이터는 n8n 웹훅에서 실시간 제공)
```

## 빌드

```bash
npm run build
```
