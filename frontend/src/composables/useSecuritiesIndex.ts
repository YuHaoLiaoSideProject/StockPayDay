/**
 * useSecuritiesIndex — 證券代號→名稱 對照表
 *
 * 從 `api/securities-index.json` 載入一次，快取於 module-level，
 * 提供 code → name 的快速查表。
 */
import { ref, computed } from 'vue'

interface SecurityEntry {
  code: string
  name: string
}

const INDEX_URL = './api/securities-index.json'

/** module-level singleton */
const entries = ref<SecurityEntry[]>([])
const loaded = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

let fetchPromise: Promise<void> | null = null

async function ensureLoaded(): Promise<void> {
  if (loaded.value) return
  if (fetchPromise) return fetchPromise
  
  fetchPromise = (async () => {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(INDEX_URL)
      if (!res.ok) throw new Error(`載入證券索引失敗: ${res.status}`)
      const data = await res.json()
      if (Array.isArray(data)) {
        entries.value = data as SecurityEntry[]
        loaded.value = true
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '載入失敗'
    } finally {
      loading.value = false
      fetchPromise = null
    }
  })()
  
  return fetchPromise
}



/**
 * 證券索引 composable
 *
 * @returns nameByCode — 以 code 查 name 的 Map
 * @returns getName    — 直接回傳名稱（找不到時回傳 code）
 */
export function useSecuritiesIndex() {
  const nameByCode = computed(() => {
    const map = new Map<string, string>()
    for (const entry of entries.value) {
      map.set(entry.code, entry.name)
    }
    return map
  })

  function getName(code: string): string {
    return nameByCode.value.get(code) ?? code
  }

  return {
    entries,
    loaded,
    loading,
    error,
    nameByCode,
    getName,
    reload: ensureLoaded,
  }
}

/** 測試用：重置 module-level 狀態 */
export function resetSecuritiesIndex(): void {
  entries.value = []
  loaded.value = false
  loading.value = false
  error.value = null
  fetchPromise = null
}
