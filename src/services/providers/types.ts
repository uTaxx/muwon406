import type { Restaurant } from '../../types/restaurant'

export interface SearchProvider {
  readonly name: string
  /**
   * keyword/region으로 원본 결과를 가져옵니다. 카테고리/정렬/부가 필터는
   * App.tsx에서 filterAndSortRestaurants로 한 번에 적용하므로 여기서는
   * 신경 쓰지 않아도 됩니다 — 이렇게 해야 그 필터들만 바뀔 때 provider를
   * 다시 호출하지 않습니다 (실시간 API 호출/쓰기 비용이 있는 provider에 중요).
   */
  search(keyword: string, region: string): Promise<Restaurant[]>
}
