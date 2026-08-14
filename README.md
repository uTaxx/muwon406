# 맛집·카페 검색 대시보드

키워드/지역으로 맛집·카페를 검색하고, 지도에서 위치를 확인하고, 평점·리뷰순으로 정렬하고, 즐겨찾기(찜)할 수 있는 대시보드입니다.

## 주요 기능

- 키워드/지역 검색 (가게명, 메뉴, 태그, 지역명, 주소)
- 음식 종류별 세부 카테고리 필터 (숯불구이, 철판구이, 한식, 디저트카페 등)
- 평점순 / 리뷰 많은순 / 거리순 / 가격 낮은순 정렬
- 즐겨찾기(찜) — 브라우저 localStorage에 저장되어 새로고침해도 유지
- 카카오맵 연동 (API 키 설정 시 실제 지도에 마커 표시)
- 체험단/협찬 리뷰 이벤트 진행 중인 곳 제외 필터
- 광고성 리뷰 비율이 높은(40% 이상) 곳 제외 필터

### 리뷰 품질 필터에 대해

`Restaurant` 데이터에는 `hasReviewEvent`(체험단/협찬 진행 여부)와 `sponsoredReviewRatio`(광고성 리뷰 추정 비율, 0~100)
필드가 있습니다. 지금은 샘플 데이터에 값이 채워져 있어 필터가 바로 동작하지만, 실제 값은 블로그 리뷰 본문을 수집해
광고/협찬 표기나 문체를 분석하는 별도 파이프라인이 있어야 채울 수 있습니다. 카카오/네이버/구글 provider는 아직
이 신호를 제공하지 않아 기본값(`false`, `0`)으로 채워집니다 — 실제 서비스에서 이 필터를 쓰려면 리뷰 크롤링·분류
로직을 추가해 이 두 필드를 채워주세요.

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

## 프로젝트 구조

```
src/
  types/restaurant.ts        # 맛집/카페 데이터 타입 정의
  data/mockRestaurants.ts    # 샘플 데이터 (실제 API 응답과 동일한 필드 구조)
  utils/filterRestaurants.ts # 키워드/지역/카테고리 필터 + 정렬 로직
  services/providers/        # 데이터 소스 추상화 (mock/kakao/naver/google)
  hooks/                     # 즐겨찾기(localStorage), 카카오맵 SDK 로더
  components/                # 검색바, 필터, 정렬, 카드, 지도, 즐겨찾기 패널
  App.tsx                    # 전체 레이아웃 및 상태 관리
```

## 빌드

```bash
npm run build
```
