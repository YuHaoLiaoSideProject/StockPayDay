import { ref, computed } from 'vue'
import type { UpcomingDividend, LoadingStatus } from '../types/stock'

// --- Module-level singleton state ---
const upcoming = ref<UpcomingDividend[]>([])
const status = ref<LoadingStatus>('loading')
const errorMessage = ref<string>('')

/**
 * 載入 upcoming.json
 * 失敗時設定 status = 'error'
 */
async function load(): Promise<void> {
  status.value = 'loading'
  errorMessage.value = ''

  try {
    const response = await fetch('../api/upcoming.json')
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data: UpcomingDividend[] = await response.json()
    upcoming.value = data
    status.value = data.length === 0 ? 'empty' : 'success'
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
 * 載入 api/upcoming.json 並提供篩選功能。
 * 靜態站部署，fetch 相對路徑即可。
 */
export function useUpcoming() {

  /**
   * 重新載入（重試）
   */
  async function retry(): Promise<void> {
    await load()
  }

  /**
   * 依日期取得配息資料
   * @param dateStr YYYY-MM-DD
   */
  function getByDate(dateStr: string): UpcomingDividend[] {
    return upcoming.value.filter(item => item.ex_date === dateStr)
  }

  /**
   * 依日期排序的配息列表（近的在前）
   */
  const sortedUpcoming = computed(() => {
    return [...upcoming.value].sort(
      (a, b) => a.ex_date.localeCompare(b.ex_date)
    )
  })

  /**
   * 所有有配息的日期集合（YYYY-MM-DD）
   */
  const dividendDates = computed(() => {
    return new Set(upcoming.value.map(item => item.ex_date))
  })

  return {
    upcoming,
    status,
    errorMessage,
    load,
    retry,
    getByDate,
    sortedUpcoming,
    dividendDates,
  }
}
