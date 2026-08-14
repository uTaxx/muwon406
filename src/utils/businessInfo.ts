import type { Restaurant } from '../types/restaurant'
import { OWNER_CHANGE_YEAR_GAP_THRESHOLD } from '../types/restaurant'

export function getYearsInBusiness(restaurant: Restaurant, currentYear: number = new Date().getFullYear()): number | undefined {
  if (!restaurant.openedYear) return undefined
  return Math.max(currentYear - restaurant.openedYear, 0)
}

interface OwnerChangeEstimate {
  likely: boolean
  registeredYear?: number
}

/**
 * 개업 연도보다 사업자등록일이 한참 늦으면 중간에 주인이 바뀌었을 가능성으로 추정합니다.
 * 국세청 API는 등록번호별 현재 상태/등록일만 제공하고 소유권 변경 이력은 제공하지 않기
 * 때문에, 실제 이력이 아니라 정황상 추정치입니다.
 */
export function estimateOwnerChange(restaurant: Restaurant): OwnerChangeEstimate {
  if (!restaurant.openedYear || !restaurant.businessRegistrationDate) {
    return { likely: false }
  }
  const registeredYear = Number(restaurant.businessRegistrationDate.slice(0, 4))
  const likely = registeredYear - restaurant.openedYear >= OWNER_CHANGE_YEAR_GAP_THRESHOLD
  return { likely, registeredYear: likely ? registeredYear : undefined }
}
