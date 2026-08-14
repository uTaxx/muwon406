import type { CuisineCategory, PlaceType } from '../types/restaurant'

const ALL_CATEGORIES: CuisineCategory[] = [
  '숯불구이',
  '철판구이',
  '한식',
  '중식',
  '일식',
  '양식',
  '분식',
  '고기/구이',
  '해산물',
  '치킨',
  '디저트카페',
  '브런치카페',
  '베이커리카페',
  '스터디카페',
  '루프탑카페',
]

interface CategoryFilterProps {
  placeType: PlaceType | '전체'
  categories: CuisineCategory[]
  onPlaceTypeChange: (value: PlaceType | '전체') => void
  onCategoriesChange: (value: CuisineCategory[]) => void
}

export function CategoryFilter({
  placeType,
  categories,
  onPlaceTypeChange,
  onCategoriesChange,
}: CategoryFilterProps) {
  function toggleCategory(category: CuisineCategory) {
    if (categories.includes(category)) {
      onCategoriesChange(categories.filter((c) => c !== category))
    } else {
      onCategoriesChange([...categories, category])
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        {(['전체', '맛집', '카페'] as const).map((type) => (
          <button
            key={type}
            onClick={() => onPlaceTypeChange(type)}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold transition-colors ${
              placeType === type
                ? 'bg-brand-300 text-stone-900'
                : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
            }`}
          >
            {type}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {ALL_CATEGORIES.map((category) => (
          <button
            key={category}
            onClick={() => toggleCategory(category)}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              categories.includes(category)
                ? 'border-brand-300 bg-brand-100 text-brand-800'
                : 'border-stone-300 text-stone-600 hover:border-brand-300'
            }`}
          >
            {category}
          </button>
        ))}
      </div>
    </div>
  )
}
