import type { SearchProvider } from './types'
import type { SearchFilters } from '../../types/restaurant'

// 네이버 검색 API는 Client Secret을 요구하고 브라우저에서 직접 호출 시
// CORS로 차단됩니다. 실제 사용을 위해서는 아래와 같은 서버 프록시가 필요합니다:
//   1) Node/Express, Next.js API Route 등으로 /api/search/naver 엔드포인트를 만들고
//   2) 서버에서 X-Naver-Client-Id / X-Naver-Client-Secret 헤더를 붙여
//      https://openapi.naver.com/v1/search/local.json 을 호출한 뒤 결과를 그대로 반환
//   3) 이 provider의 fetch 대상을 그 프록시 엔드포인트(`/api/search/naver`)로 변경
export const naverProvider: SearchProvider = {
  name: 'naver',
  async search(_filters: SearchFilters) {
    throw new Error(
      '네이버 검색은 브라우저에서 직접 호출할 수 없습니다. 서버 프록시를 구성한 뒤 ' +
        'src/services/providers/naverProvider.ts 의 fetch 대상을 프록시 URL로 변경하세요.',
    )
  },
}
