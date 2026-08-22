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
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { days } = useCalendar(dividendDates, upcoming)

    expect(days.value.length).toBeGreaterThanOrEqual(35)
    expect(days.value.length).toBeLessThanOrEqual(42)
  })

  it('should have correct day structure', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { days } = useCalendar(dividendDates, upcoming)

    const firstDay = days.value[0]
    expect(firstDay).toHaveProperty('date')
    expect(firstDay).toHaveProperty('isCurrentMonth')
    expect(firstDay).toHaveProperty('isToday')
    expect(firstDay).toHaveProperty('hasDividend')
    expect(firstDay).toHaveProperty('dividends')
  })

  it('should display correct month label', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { monthLabel } = useCalendar(dividendDates, upcoming)

    expect(monthLabel.value).toBe('2026 年 7 月')
  })

  it('should navigate to previous month', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { monthLabel, prevMonth } = useCalendar(dividendDates, upcoming)

    prevMonth()
    expect(monthLabel.value).toBe('2026 年 6 月')
  })

  it('should navigate to next month', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { monthLabel, nextMonth } = useCalendar(dividendDates, upcoming)

    nextMonth()
    expect(monthLabel.value).toBe('2026 年 8 月')
  })

  it('should mark dates with dividends', () => {
    const dividendDates = ref(new Set(['2026-07-25']))
    const upcoming = ref<UpcomingDividend[]>([
      { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
    ])

    const { days } = useCalendar(dividendDates, upcoming)

    const dividendDay = days.value.find(d => d.date === '2026-07-25')
    expect(dividendDay?.hasDividend).toBe(true)
    expect(dividendDay?.dividends).toHaveLength(1)
  })

  it('should mark today correctly', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { days } = useCalendar(dividendDates, upcoming)

    const today = days.value.find(d => d.isToday)
    expect(today?.date).toBe('2026-07-15')
  })

  it('should fill trailing next-month days with correct consecutive dates', () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { days } = useCalendar(dividendDates, upcoming)

    // 所有格子必須是連續日期（相鄰兩格相差一天），
    // 且下月補齊的第一格必須是下月 1 日（2026-08-01）
    const dates = days.value.map(d => d.date)
    expect(dates).toContain('2026-08-01')

    const toTime = (s: string) => new Date(`${s}T00:00:00`).getTime()
    const dayMs = 24 * 60 * 60 * 1000
    for (let i = 1; i < dates.length; i++) {
      expect(toTime(dates[i]) - toTime(dates[i - 1])).toBe(dayMs)
      expect(dates[i]).not.toBe(dates[i - 1])
    }
  })

  it('should update when dividendDates ref changes', async () => {
    const dividendDates = ref(new Set<string>())
    const upcoming = ref<UpcomingDividend[]>([])

    const { days } = useCalendar(dividendDates, upcoming)

    // Initially no dividends
    const day25Before = days.value.find(d => d.date === '2026-07-25')
    expect(day25Before?.hasDividend).toBe(false)

    // Update dividendDates
    dividendDates.value = new Set(['2026-07-25'])
    upcoming.value = [
      { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
    ]

    // Should now have dividend
    const day25After = days.value.find(d => d.date === '2026-07-25')
    expect(day25After?.hasDividend).toBe(true)
  })
})
