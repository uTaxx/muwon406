// 같은 입력(가게 id 등)에 대해 항상 같은 결과를 주는 시드 기반 난수 생성기입니다.
// 리뷰 샘플 개수를 바꿔도 이미 보여준 리뷰 순서가 흔들리지 않도록 사용합니다.
export function createSeededRandom(seed: string): () => number {
  let h = 1779033703 ^ seed.length
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353)
    h = (h << 13) | (h >>> 19)
  }
  return function random() {
    h = Math.imul(h ^ (h >>> 16), 2246822507)
    h = Math.imul(h ^ (h >>> 13), 3266489909)
    h ^= h >>> 16
    return (h >>> 0) / 4294967296
  }
}
