import type { SearchProvider } from './types'

// 구글 Places API 키는 브라우저에 노출 시 도용 위험이 크고, 과금이 발생합니다.
// 실제 사용을 위해서는 서버 프록시를 구성하세요:
//   1) 서버에서 Places API(New) Text Search (`https://places.googleapis.com/v1/places:searchText`)를
//      X-Goog-Api-Key 헤더로 호출
//   2) 결과를 이 앱의 Restaurant 형태로 변환해 /api/search/google 로 반환
//   3) 이 provider의 fetch 대상을 그 프록시 엔드포인트로 변경
export const googleProvider: SearchProvider = {
  name: 'google',
  async search() {
    throw new Error(
      '구글 검색은 브라우저에서 직접 호출하지 않는 것을 권장합니다. 서버 프록시를 구성한 뒤 ' +
        'src/services/providers/googleProvider.ts 의 fetch 대상을 프록시 URL로 변경하세요.',
    )
  },
}
