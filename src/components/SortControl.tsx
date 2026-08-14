import type { SortKey } from '../types/restaurant'

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'rating', label: '평점순' },
  { value: 'reviewCount', label: '리뷰 많은순' },
  { value: 'distance', label: '거리순' },
  { value: 'priceAsc', label: '가격 낮은순' },
]

interface SortControlProps {
  value: SortKey
  onChange: (value: SortKey) => void
  resultCount: number
}

export function SortControl({ value, onChange, resultCount }: SortControlProps) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-neutral-500">검색 결과 {resultCount}곳</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as SortKey)}
        className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm outline-none focus:border-brand-500"
      >
        {SORT_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}
