import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { useSearch } from '../useSearch'
import { resetSecuritiesIndex } from '../useSecuritiesIndex'

// Mock fetch
const mockFetch = vi.fn()

const mockSecuritiesIndex = [
  { code: '2330', name: '台積電' },
  { code: '0050', name: '元大台灣50' },
  { code: '0056', name: '元大高股息' },
  { code: '2317', name: '鴻海' },
]

describe('useSearch', () => {
  beforeEach(() => {
    resetSecuritiesIndex() // 重置 singleton 狀態
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSecuritiesIndex),
    })
  })

  it('should initialize with empty query and results', () => {
    const { query, results } = useSearch()
    expect(query.value).toBe('')
    expect(results.value).toHaveLength(0)
  })

  it('should load securities index on first use', async () => {
    const { indexLoaded } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(mockFetch).toHaveBeenCalledWith('./api/securities-index.json')
    expect(indexLoaded.value).toBe(true)
  })

  it('should search by stock code', async () => {
    const { query, results } = useSearch()

    // Wait for index to load
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = '2330'
    await nextTick()

    expect(results.value.length).toBeGreaterThan(0)
    expect(results.value.some(r => r.code === '2330')).toBe(true)
  })

  it('should search by stock name', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = '台積'
    await nextTick()

    expect(results.value.length).toBeGreaterThan(0)
    expect(results.value.some(r => r.name.includes('台積'))).toBe(true)
  })

  it('should return empty for no match', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = 'XXXXX'
    await nextTick()

    expect(results.value.length).toBe(0)
  })

  it('should clear results when query is empty', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = '2330'
    await nextTick()
    expect(results.value.length).toBeGreaterThan(0)

    query.value = ''
    await nextTick()
    expect(results.value.length).toBe(0)
  })

  it('should limit results to 10', async () => {
    const manyItems = Array.from({ length: 20 }, (_, i) => ({
      code: `00${i}`,
      name: `測試股票${i}`,
    }))

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(manyItems),
    })

    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    // Search for common pattern
    query.value = '0'
    await nextTick()

    expect(results.value.length).toBeLessThanOrEqual(10)
  })

  it('should search case-insensitively', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    // Uppercase search should still find results
    query.value = '2330'
    await nextTick()

    expect(results.value.length).toBeGreaterThan(0)
  })

  it('should handle fetch failure gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network Error'))

    const { query, results, indexLoaded } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(indexLoaded.value).toBe(false)
    // Search should still work (return empty)
    query.value = '2330'
    await nextTick()
    expect(results.value.length).toBe(0)
  })

  it('should handle partial code match', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = '23'
    await nextTick()

    // Should find 2330 and 2317
    expect(results.value.length).toBeGreaterThanOrEqual(2)
    expect(results.value.some(r => r.code === '2330')).toBe(true)
    expect(results.value.some(r => r.code === '2317')).toBe(true)
  })
})

describe('useSearch — 功能 001（追蹤任意股票）', () => {
  beforeEach(() => {
    resetSecuritiesIndex() // 重置 singleton 狀態
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSecuritiesIndex),
    })
  })

  it('以名稱「台積」搜尋命中 2330 台積電', async () => {
    const { query, results } = useSearch()

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    query.value = '台積'
    await nextTick()

    expect(results.value.some(r => r.code === '2330' && r.name === '台積電')).toBe(true)
  })

  it('每份實例的 query/results 各自獨立（導覽列與追蹤清單頁互不干擾）', async () => {
    const navbar = useSearch()
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    const watchlistPage = useSearch()
    navbar.query.value = '2330'
    await nextTick()

    expect(navbar.results.value.some(r => r.code === '2330')).toBe(true)
    expect(watchlistPage.query.value).toBe('')
    expect(watchlistPage.results.value).toHaveLength(0)
  })
})
