const OPTIONS = [5, 10, 20, 30, 50]

interface ReviewSampleSizeControlProps {
  value: number
  onChange: (value: number) => void
}

export function ReviewSampleSizeControl({ value, onChange }: ReviewSampleSizeControlProps) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-stone-600">
      리뷰 분석 개수
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rounded-full border border-stone-300 bg-white px-2.5 py-1 text-xs text-stone-700 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-200"
      >
        {OPTIONS.map((n) => (
          <option key={n} value={n}>
            {n}개
          </option>
        ))}
      </select>
    </label>
  )
}
