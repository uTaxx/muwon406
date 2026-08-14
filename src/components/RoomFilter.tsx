interface RoomFilterProps {
  requirePrivateRoom: boolean
  onChange: (value: boolean) => void
}

export function RoomFilter({ requirePrivateRoom, onChange }: RoomFilterProps) {
  return (
    <label className="flex cursor-pointer items-center gap-1.5 text-xs text-stone-600">
      <input
        type="checkbox"
        className="accent-brand-500"
        checked={requirePrivateRoom}
        onChange={(e) => onChange(e.target.checked)}
      />
      회식용 룸 있는 곳만 보기
    </label>
  )
}
