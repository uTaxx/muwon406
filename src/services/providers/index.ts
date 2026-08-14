import type { DataSource } from '../../types/restaurant'
import type { SearchProvider } from './types'
import { mockProvider } from './mockProvider'
import { liveProvider } from './liveProvider'
import { kakaoProvider } from './kakaoProvider'
import { naverProvider } from './naverProvider'
import { googleProvider } from './googleProvider'

const providers: Record<DataSource, SearchProvider> = {
  mock: mockProvider,
  live: liveProvider,
  kakao: kakaoProvider,
  naver: naverProvider,
  google: googleProvider,
}

const configuredSource = (import.meta.env.VITE_DATA_SOURCE as DataSource | undefined) ?? 'mock'

export function getActiveProvider(): SearchProvider {
  return providers[configuredSource] ?? mockProvider
}

export function getProvider(source: DataSource): SearchProvider {
  return providers[source]
}
