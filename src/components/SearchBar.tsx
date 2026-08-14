interface SearchBarProps {
  keyword: string
  region: string
  onKeywordChange: (value: string) => void
  onRegionChange: (value: string) => void
}

export function SearchBar({ keyword, region, onKeywordChange, onRegionChange }: SearchBarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-neutral-500">키워드</label>
        <input
          type="text"
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
          placeholder="가게 이름, 메뉴, 태그로 검색 (예: 숯불, 브런치)"
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        />
      </div>
      <div className="sm:w-56">
        <label className="mb-1 block text-xs font-medium text-neutral-500">지역</label>
        <input
          type="text"
          value={region}
          onChange={(e) => onRegionChange(e.target.value)}
          placeholder="예: 홍대, 성수동"
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        />
      </div>
    </div>
  )
}
