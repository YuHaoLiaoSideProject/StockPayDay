import { ref, watch, type Ref } from 'vue'

/** 單筆歷史配息紀錄 */
interface DividendHistory {
  year: number
  ex_date: string
  cash_dividend?: number
  stock_dividend?: number
}

/** 證券歷史配息資料 */
interface StockDetail {
  code: string
  name: string
  history: DividendHistory[]
}

/**
 * 載入單支證券歷史配息資料
 *
 * 從 `api/securities/{code}.json` 讀取，
 * 回傳 stock 資料、loading 狀態、error 訊息。
 */
export function useStock(code: Ref<string>) {
  const stock = ref<StockDetail | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  // 監聽 code 變化，重新載入資料
  watch(code, () => fetchStock(), { immediate: true })

  async function fetchStock(): Promise<void> {
    if (!code.value) return
    loading.value = true
    error.value = null
    stock.value = null

    try {
      const res = await fetch(`../api/securities/${code.value}.json`)
      if (!res.ok) {
        throw new Error('找不到該證券資料')
      }
      stock.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '資料載入失敗'
    } finally {
      loading.value = false
    }
  }

  return { stock, loading, error }
}
