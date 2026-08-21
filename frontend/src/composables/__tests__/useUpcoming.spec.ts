import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useUpcoming } from '../useUpcoming'

describe('useUpcoming', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('should initialize with loading status', () => {
    const { status, upcoming } = useUpcoming()
    expect(status.value).toBe('loading')
    expect(upcoming.value).toEqual([])
  })

  it('should load upcoming data successfully', async () => {
    const mockData = [
      {
        code: '2330',
        name: '台積電',
        type: 'stock' as const,
        ex_date: '2026-07-25',
        pay_date: '2026-08-15',
        dividend: 3.5,
      },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const { load, status, upcoming } = useUpcoming()
    await load()

    expect(status.value).toBe('success')
    expect(upcoming.value).toEqual(mockData)
  })

  it('should handle fetch error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    const { load, status, errorMessage } = useUpcoming()
    await load()

    expect(status.value).toBe('error')
    expect(errorMessage.value).toBe('資料載入失敗，請稍後再試')
  })

  it('should handle HTTP error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
    }))

    const { load, status } = useUpcoming()
    await load()

    expect(status.value).toBe('error')
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
    const mockData = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-07-20', pay_date: '2026-08-10', dividend: 1.8 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const { load, getByDate } = useUpcoming()
    await load()

    const result = getByDate('2026-07-25')
    expect(result).toHaveLength(1)
    expect(result[0].code).toBe('2330')
  })

  it('should sort upcoming by date', async () => {
    const mockData = [
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-08-01', pay_date: '2026-09-01', dividend: 1.8 },
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const { load, sortedUpcoming } = useUpcoming()
    await load()

    expect(sortedUpcoming.value[0].ex_date).toBe('2026-07-25')
    expect(sortedUpcoming.value[1].ex_date).toBe('2026-08-01')
  })

  it('should return correct dividendDates set', async () => {
    const mockData = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
      { code: '0056', name: '元大高股息', type: 'etf' as const, ex_date: '2026-07-25', pay_date: '2026-08-10', dividend: 1.8 },
    ]

    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    }))

    const { load, dividendDates } = useUpcoming()
    await load()

    expect(dividendDates.value.size).toBe(1)
    expect(dividendDates.value.has('2026-07-25')).toBe(true)
  })

  it('should retry loading', async () => {
    const mockData = [
      { code: '2330', name: '台積電', type: 'stock' as const, ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
    ]

    vi.stubGlobal('fetch', vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockData),
      }))

    const { load, retry, status } = useUpcoming()
    await load()
    expect(status.value).toBe('error')

    await retry()
    expect(status.value).toBe('success')
  })
})
