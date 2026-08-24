import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useUpcoming } from '../useUpcoming'

describe('useUpcoming', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('should load monthly dividend data successfully', async () => {
    const mockJuly = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 },
    ]
    const mockAug = [
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-08-01', pay_date: '2026-09-01', cash_dividend: 1.8, stock_dividend: 0 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-07', '2026-08'] }) })
      if (url.includes('2026-07')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockJuly) })
      if (url.includes('2026-08')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAug) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, status, getMonthData } = useUpcoming()
    await load()

    expect(status.value).toBe('success')
    expect(getMonthData(2026, 7)).toEqual(mockJuly)
    expect(getMonthData(2026, 8)).toEqual(mockAug)
  })

  it('should handle fetch error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    const { load, status } = useUpcoming()
    await load()

    expect(status.value).toBe('error')
  })

  it('should handle HTTP error gracefully (some months fail, some succeed)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-08', '2026-09'] }) })
      if (url.includes('2026-09')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve([{ code: '2330', name: '台積電', type: 'stock', ex_date: '2026-09-16', pay_date: '2026-10-08', cash_dividend: 7.0, stock_dividend: 0 }]) })
      }
      return Promise.resolve({ ok: false, status: 404 })
    }))

    const { load, status } = useUpcoming()
    await load()

    // At least one month succeeded → success
    expect(status.value).toBe('success')
  })

  it('should set empty status when no data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    }))

    const { load, status } = useUpcoming()
    await load()

    expect(status.value).toBe('empty')
  })

  it('should filter by date with getByDate', async () => {
    const mockJuly = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 },
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-07-20', pay_date: '2026-08-10', cash_dividend: 1.8, stock_dividend: 0 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-07'] }) })
      if (url.includes('2026-07')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockJuly) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, getByDate } = useUpcoming()
    await load()

    const result = getByDate('2026-07-25')
    expect(result).toHaveLength(1)
    expect(result[0].code).toBe('2330')
  })

  it('should compute upcoming (future only)', async () => {
    // Use dates relative to current year so they're loaded
    const now = new Date()
    const year = now.getFullYear()
    const futureMonth = String(now.getMonth() + 2 > 12 ? 1 : now.getMonth() + 2).padStart(2, '0')
    const pastMonth = String(now.getMonth() > 1 ? now.getMonth() - 1 : 12).padStart(2, '0')
    const futureYear = now.getMonth() + 2 > 12 ? year + 1 : year
    const pastYear = now.getMonth() > 1 ? year : year - 1

    const futureDate = `${futureYear}-${futureMonth}-15`
    const pastDate = `${pastYear}-${pastMonth}-15`

    const mockFuture = [
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: futureDate, pay_date: futureDate, cash_dividend: 1.8, stock_dividend: 0 },
    ]
    const mockPast = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: pastDate, pay_date: pastDate, cash_dividend: 3.5, stock_dividend: 0 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: [`${futureYear}-${futureMonth}`, `${pastYear}-${pastMonth}`] }) })
      const match = url.match(/(\d{4}-\d{2})/)
      const month = match?.[1]
      if (month === `${futureYear}-${futureMonth}`) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockFuture) })
      if (month === `${pastYear}-${pastMonth}`) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockPast) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, upcoming } = useUpcoming()
    await load()

    expect(upcoming.value).toHaveLength(1)
    expect(upcoming.value[0].ex_date).toBe(futureDate)
  })

  it('should sort upcoming by date', async () => {
    const mockSep = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-09-16', pay_date: '2026-10-08', cash_dividend: 7.0, stock_dividend: 0 },
    ]
    const mockOct = [
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-10-14', pay_date: '2026-11-01', cash_dividend: 1.8, stock_dividend: 0 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-09', '2026-10'] }) })
      if (url.includes('2026-09')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockSep) })
      if (url.includes('2026-10')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockOct) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, sortedUpcoming } = useUpcoming()
    await load()

    // Both are future dates, sorted ascending
    expect(sortedUpcoming.value[0].ex_date).toBe('2026-09-16')
    expect(sortedUpcoming.value[1].ex_date).toBe('2026-10-14')
  })

  it('should return correct dividendDates set', async () => {
    const mockJuly = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 },
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-07-25', pay_date: '2026-08-10', cash_dividend: 1.8, stock_dividend: 0 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-07'] }) })
      if (url.includes('2026-07')) return Promise.resolve({ ok: true, json: () => Promise.resolve(mockJuly) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, dividendDates } = useUpcoming()
    await load()

    expect(dividendDates.value.size).toBe(1)
    expect(dividendDates.value.has('2026-07-25')).toBe(true)
  })

  it('should retry loading', async () => {
    const mockData = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-09-16', pay_date: '2026-10-08', cash_dividend: 7.0, stock_dividend: 0 },
    ]

    // First load: all fail → error
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    const { load, retry, status } = useUpcoming()
    await load()
    expect(status.value).toBe('error')

    // Retry: index.json returns month list, then month data
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-09'] }) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockData) })
    }))

    await retry()
    expect(status.value).toBe('success')
  })

  it('should getMonthData return empty for unknown month', async () => {
    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('index.json')) return Promise.resolve({ ok: true, json: () => Promise.resolve({ months: ['2026-08'] }) })
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) })
    }))

    const { load, getMonthData } = useUpcoming()
    await load()

    expect(getMonthData(2025, 1)).toEqual([])
  })
})
