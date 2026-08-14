const OPTIONS = [5, 10, 20, 30, 50]

interface ReviewSampleSizeControlProps {
  value: number
  onChange: (value: number) => void
}

export function ReviewSampleSizeControl({ value, onChange }: ReviewSampleSizeControlProps) {
  return (
    <label className="flex items-center gap-1.5 text-xs text-neutral-600">
      리뷰 분석 개수
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="rounded border border-neutral-300 px-1.5 py-1 text-xs outline-none focus:border-brand-500"
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
