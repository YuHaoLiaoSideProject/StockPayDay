import { ref, computed, type Ref } from 'vue'
import type { CalendarDay, UpcomingDividend } from '../types/stock'

/**
 * 行事曆管理 composable
 *
 * 計算當月日曆格子（含前後月補齊），
 * 標記有配息的日期。
 *
 * 直接從 allMonths reactive ref 讀取當月配息資料，
 * 切換月份時自動重新計算。
 */
export function useCalendar(
  allMonths: Ref<Map<string, UpcomingDividend[]>>
) {
  const currentDate = ref(new Date())

  /** 當前年月標題，如 "2026 年 7 月" */
  const monthLabel = computed(() => {
    const d = currentDate.value
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`
  })

  /** 產生行事曆格子（最多 6 週 = 42 格） */
  const days = computed<CalendarDay[]>(() => {
    const d = currentDate.value
    const year = d.getFullYear()
    const month = d.getMonth()

    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)

    const startWeekday = firstDay.getDay()
    const totalDays = lastDay.getDate()

    const today = new Date()
    const todayStr = formatDate(today)

    const monthKey = `${year}-${String(month + 1).padStart(2, '0')}`
    const currentMonthData = allMonths.value.get(monthKey) ?? []
    const calDividendDates = new Set(currentMonthData.map(item => item.ex_date))

    const result: CalendarDay[] = []

    // 補齊前月
    for (let i = startWeekday - 1; i >= 0; i--) {
      const date = new Date(year, month, -i)
      result.push(createDay(date, todayStr, year, month, calDividendDates, currentMonthData))
    }

    // 當月
    for (let d = 1; d <= totalDays; d++) {
      const date = new Date(year, month, d)
      result.push(createDay(date, todayStr, year, month, calDividendDates, currentMonthData))
    }

    // 補齊後月（確保至少 35 格 = 5 週）
    while (result.length < 35) {
      const date = new Date(year, month, result.length - startWeekday + 1)
      result.push(createDay(date, todayStr, year, month, calDividendDates, currentMonthData))
    }

    return result
  })

  /** 切換到上個月 */
  function prevMonth(): void {
    const d = currentDate.value
    currentDate.value = new Date(d.getFullYear(), d.getMonth() - 1, 1)
  }

  /** 切換到下個月 */
  function nextMonth(): void {
    const d = currentDate.value
    currentDate.value = new Date(d.getFullYear(), d.getMonth() + 1, 1)
  }

  return { currentDate, monthLabel, days, prevMonth, nextMonth }
}

/** 格式化日期為 YYYY-MM-DD */
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 建立單日格子 */
function createDay(
  date: Date,
  todayStr: string,
  currentYear: number,
  currentMonth: number,
  dividendDates: Set<string>,
  upcoming: UpcomingDividend[]
): CalendarDay {
  const dateStr = formatDate(date)

  return {
    date: dateStr,
    isCurrentMonth: date.getMonth() === currentMonth && date.getFullYear() === currentYear,
    isToday: dateStr === todayStr,
    hasDividend: dividendDates.has(dateStr),
    dividends: upcoming.filter(item => item.ex_date === dateStr),
  }
}
