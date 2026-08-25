import { ref, computed } from 'vue'
import type { UpcomingDividend, LoadingStatus } from '../types/stock'

// --- Module-level singleton state ---
const allMonths = ref<Map<string, UpcomingDividend[]>>(new Map())
const status = ref<LoadingStatus>('loading')
const errorMessage = ref<string>('')

// --- Index cache for available months ---
let availableMonths: Set<string> | null = null
let lastUpdated: string | null = null

/**
 * 從月份檔案的月份 key（YYYY-MM）取得今天的 YYYY-MM
 */
function currentMonthKey(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

/**
 * 載入 index.json（記錄有哪些月份檔案）
 * 回傳可用月份列表，同時快取到模組層級
 */
async function fetchIndex(): Promise<string[]> {
  const response = await fetch('./api/dividends/index.json')
  if (!response.ok) throw new Error(`index.json HTTP ${response.status}`)
  const data = await response.json()
  const months = data.months ?? []
  availableMonths = new Set(months)
  lastUpdated = data.last_updated ?? null
  return months
}

/**
 * 檢查指定月份是否在 index.json 中存在
 * @param monthKey YYYY-MM
 */
function isMonthAvailable(monthKey: string): boolean {
  // 如果尚未載入 index，預設可用（讓 fetch 嘗試）
  if (availableMonths === null) return true
  return availableMonths.has(monthKey)
}

/**
 * 取得 index.json 的 last_updated 時間
 */
function getLastUpdated(): string | null {
  return lastUpdated
}

/**
 * 確保 index.json 已載入（快取機制）
 */
async function ensureIndexLoaded(): Promise<void> {
  if (availableMonths === null) {
    await fetchIndex()
  }
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
 * @param months 可選：指定要載入的月份（YYYY-MM），省略則載入 index.json 全部月份
 */
async function load(months?: string[]): Promise<void> {
  status.value = 'loading'
  errorMessage.value = ''

  try {
    let monthKeys: string[]

    if (months && months.length > 0) {
      // 指定月份：直接使用，不 fetch index.json
      monthKeys = months
    } else {
      // 未指定：讀取 index.json 取得全部可用品月份
      monthKeys = await fetchIndex()
      if (monthKeys.length === 0) {
        monthKeys.push(currentMonthKey())
      }
    }

    // 並行載入指定月份
    const results = await Promise.allSettled(
      monthKeys.map(key => fetchMonth(key))
    )

    // 指定月份模式：合併到現有資料；全量模式：替換
    const merged = months ? new Map(allMonths.value) : new Map<string, UpcomingDividend[]>()
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

/**
 * 確保指定月份已載入（懶載入用）
 * @param monthKey YYYY-MM
 * @returns 該月資料，載入失敗回傳空陣列
 */
async function ensureMonth(monthKey: string): Promise<UpcomingDividend[]> {
  // 已載入：直接回傳
  if (allMonths.value.has(monthKey)) {
    return allMonths.value.get(monthKey) ?? []
  }

  // 確保 index 已載入以檢查月份是否存在
  await ensureIndexLoaded()

  // 檢查月份是否在 index 中存在，不存在則直接回傳空
  if (!isMonthAvailable(monthKey)) {
    return []
  }

  // 月份存在：fetch 該月
  try {
    const data = await fetchMonth(monthKey)
    if (data.length > 0) {
      const merged = new Map(allMonths.value)
      merged.set(monthKey, data)
      allMonths.value = merged
    }
    return data
  } catch {
    return []
  }
}

// 注意：移除 module-level load()，由各 View 在 onMounted 決定載入範圍

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

  /**
   * 重置模組級別快取（測試用）
   */
  function resetCache(): void {
    allMonths.value = new Map()
    availableMonths = null
    lastUpdated = null
    status.value = 'loading'
    errorMessage.value = ''
  }

  return {
    allMonths,
    status,
    errorMessage,
    load,
    retry,
    ensureMonth,
    getMonthData,
    getByDate,
    upcoming,
    sortedUpcoming,
    dividendDates,
    isMonthAvailable,
    getLastUpdated,
    ensureIndexLoaded,
    resetCache,
  }
}
