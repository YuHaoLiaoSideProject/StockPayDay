import { ref, computed, type Ref } from 'vue'
import type { CalendarDay, UpcomingDividend } from '../types/stock'

/**
 * 行事曆管理 composable
 *
 * 計算當月日曆格子（含前後月補齊），
 * 標記有配息的日期。
 *
 * 接收 refs 以確保資料變動時 days 會重新計算。
 */
export function useCalendar(
  dividendDates: Ref<Set<string>>,
  upcoming: Ref<UpcomingDividend[]>
) {
  const currentDate = ref(new Date())

  /** 當前年月標題，如 "2026 年 7 月" */
  const monthLabel = computed(() => {
    const d = currentDate.value
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`
  })

  /**
   * 產生行事曆格子（最多 6 週 = 42 格）
   * - 第一格為當月 1 日前的補齊（isCurrentMonth = false）
   * - 最後一格為當月最後一日後的補齊
   */
  const days = computed<CalendarDay[]>(() => {
    const d = currentDate.value
    const year = d.getFullYear()
    const month = d.getMonth()

    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)

    // 1 日是星期幾（0=日, 6=六）
    const startWeekday = firstDay.getDay()
    // 當月總天數
    const totalDays = lastDay.getDate()

    const today = new Date()
    const todayStr = formatDate(today)

    // 取得當前 ref 的值
    const currentDividendDates = dividendDates.value
    const currentUpcoming = upcoming.value

    const result: CalendarDay[] = []

    // 補齊前月
    for (let i = startWeekday - 1; i >= 0; i--) {
      const date = new Date(year, month, -i)
      result.push(createDay(date, todayStr, year, month, currentDividendDates, currentUpcoming))
    }

    // 當月
    for (let d = 1; d <= totalDays; d++) {
      const date = new Date(year, month, d)
      result.push(createDay(date, todayStr, year, month, currentDividendDates, currentUpcoming))
    }

    // 補齊後月（確保至少 35 格 = 5 週）
    while (result.length < 35) {
      // result.length 已含前月補齊（startWeekday 格）與當月天數，
      // 減去後即為「下月第 N 天」（N 從 1 開始），交給 Date 自動進位到下個月
      const date = new Date(year, month, result.length - startWeekday + 1)
      result.push(createDay(date, todayStr, year, month, currentDividendDates, currentUpcoming))
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
