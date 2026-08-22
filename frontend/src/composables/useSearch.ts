import { ref, computed } from 'vue'

/** 證券索引項目 */
interface SecurityIndex {
  code: string
  name: string
}

/**
 * 即時搜尋證券 composable
 *
 * 從 `api/securities-index.json` 載入證券清單，
 * 提供 query ↔ results 即時搜尋。
 * 結果限制最多 10 筆，忽略大小寫。
 */
export function useSearch() {
  const query = ref('')
  const securitiesIndex = ref<SecurityIndex[]>([])
  const indexLoaded = ref(false)

  // 載入證券索引（僅載入一次，同步啟動）
  loadIndex()

  async function loadIndex(): Promise<void> {
    if (indexLoaded.value) return
    try {
      const res = await fetch('../api/securities-index.json')
      if (res.ok) {
        securitiesIndex.value = await res.json()
        indexLoaded.value = true
      }
    } catch {
      // 索引載入失敗，搜尋功能降級
    }
  }

  /** 重試載入證券索引（重置狀態後重新載入） */
  async function retryLoadIndex(): Promise<void> {
    indexLoaded.value = false
    await loadIndex()
  }

  /** 即時篩選結果（代號或名稱模糊匹配，忽略大小寫） */
  const results = computed(() => {
    if (!query.value.trim()) return []
    const q = query.value.trim().toLowerCase()
    return securitiesIndex.value
      .filter(
        s =>
          s.code.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q)
      )
      .slice(0, 10)
  })

  return { query, results, indexLoaded, retryLoadIndex }
}
