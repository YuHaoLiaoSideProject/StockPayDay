import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useCalendar } from '../useCalendar'
import type { UpcomingDividend } from '../../types/stock'

describe('useCalendar', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-07-15T12:00:00'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should generate calendar days for current month', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { days } = useCalendar(allMonths)

    expect(days.value.length).toBeGreaterThanOrEqual(35)
    expect(days.value.length).toBeLessThanOrEqual(42)
  })

  it('should have correct day structure', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { days } = useCalendar(allMonths)

    const firstDay = days.value[0]
    expect(firstDay).toHaveProperty('date')
    expect(firstDay).toHaveProperty('isCurrentMonth')
    expect(firstDay).toHaveProperty('isToday')
    expect(firstDay).toHaveProperty('hasDividend')
    expect(firstDay).toHaveProperty('dividends')
  })

  it('should display correct month label', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { monthLabel } = useCalendar(allMonths)

    expect(monthLabel.value).toBe('2026 年 7 月')
  })

  it('should navigate to previous month', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { monthLabel, prevMonth } = useCalendar(allMonths)

    prevMonth()
    expect(monthLabel.value).toBe('2026 年 6 月')
  })

  it('should navigate to next month', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { monthLabel, nextMonth } = useCalendar(allMonths)

    nextMonth()
    expect(monthLabel.value).toBe('2026 年 8 月')
  })

  it('should mark dates with dividends', () => {
    const mockData: UpcomingDividend[] = [
      { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 },
    ]
    const allMonths = ref(new Map([['2026-07', mockData]]))

    const { days } = useCalendar(allMonths)

    const dividendDay = days.value.find(d => d.date === '2026-07-25')
    expect(dividendDay?.hasDividend).toBe(true)
    expect(dividendDay?.dividends).toHaveLength(1)
  })

  it('should mark today correctly', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { days } = useCalendar(allMonths)

    const today = days.value.find(d => d.isToday)
    expect(today?.date).toBe('2026-07-15')
  })

  it('should fill trailing next-month days with correct consecutive dates', () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())

    const { days } = useCalendar(allMonths)

    const dates = days.value.map(d => d.date)
    expect(dates).toContain('2026-08-01')

    const toTime = (s: string) => new Date(`${s}T00:00:00`).getTime()
    const dayMs = 24 * 60 * 60 * 1000
    for (let i = 1; i < dates.length; i++) {
      expect(toTime(dates[i]) - toTime(dates[i - 1])).toBe(dayMs)
      expect(dates[i]).not.toBe(dates[i - 1])
    }
  })

  it('should reactively update when allMonths data arrives', async () => {
    const allMonths = ref(new Map<string, UpcomingDividend[]>())
    const { days } = useCalendar(allMonths)

    // Initially no dividends
    const day25Before = days.value.find(d => d.date === '2026-07-25')
    expect(day25Before?.hasDividend).toBe(false)

    // Simulate async data loading
    allMonths.value = new Map([[
      '2026-07',
      [{ code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 }],
    ]])

    // Should now have dividend
    const day25After = days.value.find(d => d.date === '2026-07-25')
    expect(day25After?.hasDividend).toBe(true)
  })

  it('should reload data when month changes', () => {
    const julyData: UpcomingDividend[] = [
      { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', cash_dividend: 3.5, stock_dividend: 0 },
    ]
    const allMonths = ref(new Map([['2026-07', julyData]]))

    const { days, nextMonth } = useCalendar(allMonths)

    // 7月有配息
    const day25Before = days.value.find(d => d.date === '2026-07-25')
    expect(day25Before?.hasDividend).toBe(true)

    // 切到8月（無配息資料）
    nextMonth()
    const day25After = days.value.find(d => d.date === '2026-08-25')
    expect(day25After?.hasDividend).toBe(false)
  })
})
