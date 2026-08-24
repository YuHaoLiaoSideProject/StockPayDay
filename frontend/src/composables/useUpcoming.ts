import { ref, computed } from 'vue'
import type { UpcomingDividend, LoadingStatus } from '../types/stock'

// --- Module-level singleton state ---
const allMonths = ref<Map<string, UpcomingDividend[]>>(new Map())
const status = ref<LoadingStatus>('loading')
const errorMessage = ref<string>('')

/**
 * 從月份檔案的月份 key（YYYY-MM）取得今天的 YYYY-MM
 */
function currentMonthKey(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

/**
 * 載入 index.json（記錄有哪些月份檔案）
 */
async function fetchIndex(): Promise<string[]> {
  const response = await fetch('./api/dividends/index.json')
  if (!response.ok) throw new Error(`index.json HTTP ${response.status}`)
  const data = await response.json()
  return data.months ?? []
}

/**
 * 載入指定月份的配息資料
 * @param monthKey YYYY-MM
 */
async function fetchMonth(monthKey: string): Promise<UpcomingDividend[]> {
  const response = await fetch(`./api/dividends/${monthKey}.json`)
  if (!response.ok) throw new Error(`${monthKey}.json HTTP ${response.status}`)
  return response.json()
}

/**
 * 載入月份配息資料
 * - 先讀取 index.json 取得可用品月份列表
 * - 並行載入所有可用品月份
 */
async function load(): Promise<void> {
  status.value = 'loading'
  errorMessage.value = ''

  try {
    // 1. 先讀取 index.json
    const monthKeys = await fetchIndex()

    // 如果 index.json 無資料或格式異常，嘗試 fallback：載入當月
    if (monthKeys.length === 0) {
      const now = currentMonthKey()
      monthKeys.push(now)
    }

    // 2. 並行載入所有可用品月份
    const results = await Promise.allSettled(
      monthKeys.map(key => fetchMonth(key))
    )

    const merged = new Map<string, UpcomingDividend[]>()
    let successCount = 0
    for (let i = 0; i < monthKeys.length; i++) {
      const result = results[i]
      if (result.status === 'fulfilled' && result.value.length > 0) {
        merged.set(monthKeys[i], result.value)
        successCount++
      }
    }

    allMonths.value = merged

    if (successCount === 0) {
      // 全部月份都失敗或無資料
      const allRejected = results.every(r => r.status === 'rejected')
      if (allRejected) {
        const firstError = results.find((r): r is PromiseRejectedResult => r.status === 'rejected')
        errorMessage.value = firstError?.reason?.message ?? '資料載入失敗，請稍後再試'
      }
      status.value = allRejected ? 'error' : 'empty'
    } else {
      status.value = 'success'
    }
  } catch (e) {
    status.value = 'error'
    errorMessage.value = '資料載入失敗，請稍後再試'
  }
}

// Fire-and-forget: load once at module import time
load()

/**
 * 配息資料管理 composable
 *
 * 從 api/dividends/YYYY-MM.json 載入月份配息資料。
 * - 行事曆：使用當月資料
 * - 列表：使用 >= 當月的所有資料（未來配息）
 * - getMonthData(year, month)：取得指定月份資料
 */
export function useUpcoming() {

  /**
   * 重新載入（重試）
   */
  async function retry(): Promise<void> {
    await load()
  }

  /**
   * 取得指定月份的配息資料
   * @param year 年份（如 2026）
   * @param month 月份（1-12）
   */
  function getMonthData(year: number, month: number): UpcomingDividend[] {
    const key = `${year}-${String(month).padStart(2, '0')}`
    return allMonths.value.get(key) ?? []
  }

  /**
   * 依日期取得配息資料（從全量月份資料中查詢）
   * @param dateStr YYYY-MM-DD
   */
  function getByDate(dateStr: string): UpcomingDividend[] {
    const monthKey = dateStr.slice(0, 7)
    const monthData = allMonths.value.get(monthKey) ?? []
    return monthData.filter(item => item.ex_date === dateStr)
  }

  /**
   * 未來配息列表（>= 今天，依 ex_date 升冪排序）
   */
  const upcoming = computed(() => {
    const today = new Date().toISOString().slice(0, 10)
    const result: UpcomingDividend[] = []
    for (const monthRecords of allMonths.value.values()) {
      for (const rec of monthRecords) {
        if (rec.ex_date >= today) {
          result.push(rec)
        }
      }
    }
    result.sort((a, b) => a.ex_date.localeCompare(b.ex_date))
    return result
  })

  /**
   * 依日期排序的配息列表（近的在前）
   */
  const sortedUpcoming = computed(() => upcoming.value)

  /**
   * 所有有配息的日期集合（YYYY-MM-DD）
   */
  const dividendDates = computed(() => {
    const dates = new Set<string>()
    for (const monthRecords of allMonths.value.values()) {
      for (const rec of monthRecords) {
        dates.add(rec.ex_date)
      }
    }
    return dates
  })

  return {
    allMonths,
    status,
    errorMessage,
    load,
    retry,
    getMonthData,
    getByDate,
    upcoming,
    sortedUpcoming,
    dividendDates,
  }
}
