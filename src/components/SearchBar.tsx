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
        <label className="mb-1 block text-xs font-medium text-stone-500">키워드</label>
        <div className="relative">
          <input
            type="text"
            value={keyword}
            onChange={(e) => onKeywordChange(e.target.value)}
            placeholder="가게 이름, 메뉴, 태그로 검색 (예: 숯불, 브런치)"
            className="w-full rounded-full border border-stone-300 bg-white py-2 pl-4 pr-10 text-sm text-stone-800 outline-none placeholder:text-stone-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200"
          />
          <svg
            className="pointer-events-none absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            aria-hidden="true"
          >
            <circle cx="9" cy="9" r="6" />
            <path d="M17 17l-4-4" strokeLinecap="round" />
          </svg>
        </div>
      </div>
      <div className="sm:w-56">
        <label className="mb-1 block text-xs font-medium text-stone-500">지역</label>
        <input
          type="text"
          value={region}
          onChange={(e) => onRegionChange(e.target.value)}
          placeholder="예: 홍대, 성수동"
          className="w-full rounded-full border border-stone-300 bg-white px-4 py-2 text-sm text-stone-800 outline-none placeholder:text-stone-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200"
        />
      </div>
    </div>
  )
}
