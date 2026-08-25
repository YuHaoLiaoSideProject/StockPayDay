import { ref } from 'vue'

/** 證券代號 → 名稱對照表 */
interface SecuritiesIndexEntry {
  code: string
  name: string
}

// --- Module-level singleton state ---
const indexMap = ref<Map<string, string>>(new Map())
const loaded = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

/**
 * 載入證券名稱對照表
 *
 * 從 `./api/securities-index.json` 讀取所有證券的 code → name 對照，
 * 供追蹤清單等模組查詢名稱。
 */
async function loadIndex(): Promise<void> {
  if (loaded.value || loading.value) return

  loading.value = true
  error.value = null

  try {
    const res = await fetch('./api/securities-index.json')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data: SecuritiesIndexEntry[] = await res.json()

    const map = new Map<string, string>()
    for (const entry of data) {
      map.set(entry.code, entry.name)
    }
    indexMap.value = map
    loaded.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : '載入失敗'
  } finally {
    loading.value = false
  }
}

// Fire-and-forget: load once at module import time
loadIndex()

/**
 * 證券名稱查詢 composable
 *
 * 提供 `getName(code)` 函式，從對照表中查找證券名稱。
 * 若對照表尚未載入或找不到，回傳 fallback（預設為 code 本身）。
 */
export function useSecuritiesIndex() {
  /**
   * 查詢證券名稱
   * @param code 證券代號
   * @param fallback 找不到時的回退值
   */
  function getName(code: string, fallback?: string): string {
    return indexMap.value.get(code) ?? fallback ?? code
  }

  return {
    indexMap,
    loaded,
    loading,
    error,
    getName,
    /** 手動重新載入 */
    reload: loadIndex,
  }
}
