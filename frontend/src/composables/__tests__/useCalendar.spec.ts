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
