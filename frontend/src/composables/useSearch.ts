import { ref, computed } from 'vue'
import { useSecuritiesIndex } from './useSecuritiesIndex'

/**
 * 即時搜尋證券 composable
 *
 * 共用 useSecuritiesIndex 的資料（避免重複 fetch），
 * 提供 query ↔ results 即時搜尋。
 * 結果限制最多 10 筆，忽略大小寫。
 */
export function useSearch() {
  const query = ref('')
  const { entries: securitiesIndex, loaded: indexLoaded, reload: retryLoadIndex } = useSecuritiesIndex()

  // 確保資料已載入
  if (!indexLoaded.value) {
    retryLoadIndex()
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
