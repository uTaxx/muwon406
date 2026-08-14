// 표시광고법상 협찬/체험단 리뷰는 대가성 여부를 명시해야 하므로, 실제로도
// "협찬", "체험단", "제공받아", "원고료" 같은 고지 문구로 감지가 가능합니다.
// 실제 서비스에서는 이 패턴 목록을 계속 보강하거나 별도 분류 모델로 교체하면 됩니다.
const SPONSORED_PATTERNS: RegExp[] = [
  /협찬/,
  /체험단/,
  /제공받[아어]/,
  /원고료/,
  /무상으로\s*제공/,
  /소정의\s*(수수료|원고료)/,
  /광고비를\s*(지원|받)/,
]

export function classifyReview(content: string): boolean {
  return SPONSORED_PATTERNS.some((pattern) => pattern.test(content))
}
