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
      <span className="text-sm text-stone-500">
        검색 결과 <span className="font-semibold text-stone-800">{resultCount}</span>곳
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as SortKey)}
        className="rounded-full border border-stone-300 bg-white px-3.5 py-1.5 text-sm text-stone-700 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-200"
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
