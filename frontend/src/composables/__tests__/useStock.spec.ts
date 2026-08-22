import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useStock } from '../useStock'

// Mock fetch
const mockFetch = vi.fn()

describe('useStock', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch)
    mockFetch.mockReset()
  })

  it('should initialize with loading state', () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ code: '2330', name: '台積電', history: [] }),
    })

    const code = ref('2330')
    const { stock, loading, error } = useStock(code)

    // Initially loading
    expect(loading.value).toBe(true)
    expect(stock.value).toBeNull()
    expect(error.value).toBeNull()
  })

  it('should load stock data by code', async () => {
    const mockData = {
      code: '2330',
      name: '台積電',
      history: [
        { year: 2026, ex_date: '2026-07-25', dividend: 3.5 },
        { year: 2025, ex_date: '2025-07-18', dividend: 3.2 },
      ],
    }
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    })

    const code = ref('2330')
    const { stock, loading, error } = useStock(code)

    await nextTick()
    // Wait for async fetch
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
    expect(stock.value).toBeDefined()
    expect(stock.value?.code).toBe('2330')
    expect(stock.value?.name).toBe('台積電')
    expect(stock.value?.history).toHaveLength(2)
  })

  it('should handle stock not found (404)', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
    })

    const code = ref('XXXXX')
    const { stock, loading, error } = useStock(code)

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(loading.value).toBe(false)
    expect(stock.value).toBeNull()
    expect(error.value).toBe('找不到該證券資料')
  })

  it('should handle network error', async () => {
    mockFetch.mockRejectedValue(new Error('Network Error'))

    const code = ref('2330')
    const { stock, loading, error } = useStock(code)

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(loading.value).toBe(false)
    expect(stock.value).toBeNull()
    expect(error.value).toBe('Network Error')
  })

  it('should handle non-Error exception', async () => {
    mockFetch.mockRejectedValue('unknown error')

    const code = ref('2330')
    const { stock, loading, error } = useStock(code)

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(loading.value).toBe(false)
    expect(stock.value).toBeNull()
    expect(error.value).toBe('資料載入失敗')
  })

  it('should call fetch with correct URL', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ code: '0050', name: '元大台灣50', history: [] }),
    })

    const code = ref('0050')
    useStock(code)

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(mockFetch).toHaveBeenCalledWith('/api/securities/0050.json')
  })

  it('should reload when code changes', async () => {
    const mockData1 = { code: '2330', name: '台積電', history: [] }
    const mockData2 = { code: '0050', name: '元大台灣50', history: [] }

    mockFetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockData1) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockData2) })

    const code = ref('2330')
    const { stock } = useStock(code)

    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))
    expect(stock.value?.code).toBe('2330')

    // Change code
    code.value = '0050'
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 10))

    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(stock.value?.code).toBe('0050')
  })
})
