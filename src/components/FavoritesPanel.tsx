import type { Restaurant } from '../types/restaurant'

interface FavoritesPanelProps {
  favorites: Restaurant[]
  onSelect: (restaurant: Restaurant) => void
  onRemove: (id: string) => void
}

export function FavoritesPanel({ favorites, onSelect, onRemove }: FavoritesPanelProps) {
  if (favorites.length === 0) {
    return <p className="text-sm text-neutral-400">아직 찜한 곳이 없어요. 카드의 ☆를 눌러보세요.</p>
  }

  return (
    <ul className="space-y-2">
      {favorites.map((place) => (
        <li
          key={place.id}
          className="flex items-center justify-between gap-2 rounded-lg border border-neutral-200 bg-white px-3 py-2"
        >
          <button onClick={() => onSelect(place)} className="min-w-0 flex-1 text-left">
            <p className="truncate text-sm font-medium text-neutral-800">{place.name}</p>
            <p className="truncate text-xs text-neutral-400">{place.region} · {place.category}</p>
          </button>
          <button
            onClick={() => onRemove(place.id)}
            aria-label="즐겨찾기 해제"
            className="shrink-0 text-neutral-300 hover:text-red-400"
          >
            ✕
          </button>
        </li>
      ))}
    </ul>
  )
}
