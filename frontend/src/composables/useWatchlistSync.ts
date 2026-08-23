/**
 * useWatchlistSync — 跨裝置追蹤清單同步引擎（Phase 9 子任務 B）
 *
 * 職責：配對碼（kvdb access token）存在時，負責本機追蹤清單與 kvdb.io 雲端
 * 文件之間的雙向同步：pull → merge → push；含 1.5s debounce 寫回、60s 前景
 * 輪詢（僅 tab visible）、focus/visibilitychange 即時讀取，以及 429 指數退避
 * （30s → 60s → 120s）。
 *
 * 選配鐵律（§1.4 / §5）：無配對碼（syncActive=false）時整個引擎不啟動，
 * syncOnce() 直接 return，不發任何請求，行為與現況 100% 一致。
 *
 * 依賴：useWatchlist（子任務 A）已擴充 module-level `syncActiveRef`；
 * 此處僅讀寫該旗標（配對 → true、停用 → false），不引入循環依賴。
 */
import { ref, computed, watchEffect, onBeforeUnmount, getCurrentInstance } from 'vue'
import type { WatchlistItem, WatchlistSyncDoc, SyncStatus } from '../types/watchlist'
import { useWatchlist, syncActiveRef } from './useWatchlist'

const TOKEN_KEY = 'stockpayday-sync-token'
const KVDB_BASE = 'https://kvdb.io'
const BUCKET = 'stockpayday'
const POLL_INTERVAL_MS = 60_000
const WRITE_DEBOUNCE_MS = 1_500
const BACKOFF_BASE_MS = 30_000
const BACKOFF_MAX_MS = 120_000

/**
 * Cloudflare Worker URL（Phase 9 §2.1）
 * 用於 createAccount()：POST { email } → 建 bucket + 產生 token
 * 部署後替換為實際 Worker URL；本地開發可用 http://localhost:8787
 */
const WORKER_URL = import.meta.env.VITE_SYNC_WORKER_URL || 'https://kvdb-proxy.your-domain.workers.dev'

/** 429 速率限制專屬錯誤：觸發指數退避排程 */
class SyncRateLimitedError extends Error {
  constructor() {
    super('rate limited')
    this.name = 'SyncRateLimitedError'
  }
}

/**
 * kvdb key：一人一份 → user:<uid>:watchlist
 * uid 於開通時由擁有者指定（見 README 開通流程）；此處以單一使用者語意簡化
 */
function kvKey(): string {
  return 'user:me:watchlist'
}

function kvdbUrl(): string {
  return `${KVDB_BASE}/${BUCKET}/${kvKey()}?access_token=${token.value}`
}

/** 讀取 localStorage 中的配對碼（讀取失敗時視同未配對，維持現況） */
function readToken(): string {
  try {
    return localStorage.getItem(TOKEN_KEY) ?? ''
  } catch {
    return ''
  }
}

// ── module-level 狀態（singleton，與 useWatchlist 同層）──
const token = ref<string>(readToken())
const status = ref<SyncStatus>('disabled')
const lastSyncedAt = ref<number | null>(null)
const lastError = ref<string | null>(null)

/** 已配對（token 非空）→ 同步引擎可運作 */
const syncActive = computed(() => token.value.length > 0)

// ── 引擎內部狀態 ──
let pollTimer: number | undefined
let debounceTimer: number | undefined
let backoffTimer: number | undefined
let backoff = 0
let inFlight = false
let listenersRegistered = false
/** 上次成功寫回雲端的 items 快照（JSON）；null = 尚未成功寫回過 */
let lastPushedSnapshot: string | null = null

/** 本地 items 是否與「上次成功寫回」不同（有待傳播的變更） */
function hasLocalChanges(): boolean {
  const { items } = useWatchlist()
  return JSON.stringify(items.value) !== lastPushedSnapshot
}

function isVisible(): boolean {
  return document.visibilityState === 'visible'
}

// ── kvdb.io 契約（§2.1）──

/** 拉取雲端文件；GET 404（首次）→ null */
async function pull(): Promise<WatchlistSyncDoc | null> {
  const res = await fetch(kvdbUrl())
  if (res.status === 404) return null // 首次：雲端尚無文件
  if (res.status === 429) throw new SyncRateLimitedError()
  if (!res.ok) throw new Error(`pull failed: ${res.status}`)
  return (await res.json()) as WatchlistSyncDoc
}

/** 寫回合併後的本地清單（POST WatchlistSyncDoc） */
async function push(items: WatchlistItem[]): Promise<void> {
  const doc: WatchlistSyncDoc = { updatedAt: Date.now(), items }
  const res = await fetch(kvdbUrl(), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(doc),
  })
  if (res.status === 429) throw new SyncRateLimitedError()
  if (!res.ok) throw new Error(`push failed: ${res.status}`)
}

/**
 * merge — 依 code 並集；單筆以 updatedAt（無則 addedAt）新者勝；
 * 同刻時墓碑（deleted: true）為最終狀態；墓碑保留在陣列中以持續傳播「移除」。
 */
export function merge(localItems: WatchlistItem[], remoteItems?: WatchlistItem[]): WatchlistItem[] {
  const byCode = new Map<string, WatchlistItem>()
  for (const item of [...(remoteItems ?? []), ...localItems]) {
    const prev = byCode.get(item.code)
    if (!prev) {
      byCode.set(item.code, item) // 新項目直接採用
      continue
    }
    const prevTs = prev.updatedAt ?? prev.addedAt
    const curTs = item.updatedAt ?? item.addedAt
    const prevDeleted = prev.deleted === true
    const curDeleted = item.deleted === true
    // 較新者勝；同刻時墓碑（deleted）為最終狀態，不被舊資料覆蓋
    if (curTs > prevTs || (curTs === prevTs && curDeleted && !prevDeleted)) {
      byCode.set(item.code, item)
    }
  }
  return [...byCode.values()]
}

// ── 同步主流程：pull → merge → push（§1.4 / §3）──
async function syncOnce(): Promise<void> {
  if (!syncActive.value) return // 未配對：零負擔，不發任何請求
  if (inFlight) return // 避免重入（輪詢/退避/debounce 疊加）
  inFlight = true
  status.value = 'syncing'
  try {
    const remote = await pull()
    const { items } = useWatchlist()
    const merged = merge(items.value, remote?.items)
    items.value = merged
    await push(merged) // 合併結果一律寫回（遠端較新或本地較新皆正確處理）
    lastPushedSnapshot = JSON.stringify(merged)
    lastSyncedAt.value = Date.now()
    lastError.value = null
    status.value = 'synced'
    backoff = 0 // 成功後退避歸零
  } catch (err) {
    if (err instanceof SyncRateLimitedError) {
      scheduleBackoff()
      lastError.value = `速率限制（429），${Math.round(backoff / 1000)} 秒後重試`
    } else {
      lastError.value = err instanceof Error ? err.message : '同步失敗'
    }
    status.value = 'error'
  } finally {
    inFlight = false
  }
}

// ── 觸發策略（§1.4 / §4）──

function clearDebounceTimer(): void {
  if (debounceTimer !== undefined) {
    clearTimeout(debounceTimer)
    debounceTimer = undefined
  }
}

function clearBackoffTimer(): void {
  if (backoffTimer !== undefined) {
    clearTimeout(backoffTimer)
    backoffTimer = undefined
  }
}

/**
 * 本地變更 → debounce 1.5s 後 syncOnce。
 * timer 觸發時再以快照比對（hasLocalChanges），確保「同步寫入 items 後若無
 * 實際變更不重複推」，杜絕自身 watchEffect 死循環。
 */
function scheduleDebouncedSync(): void {
  clearDebounceTimer()
  debounceTimer = window.setTimeout(() => {
    debounceTimer = undefined
    if (syncActive.value && hasLocalChanges()) {
      void syncOnce()
    }
  }, WRITE_DEBOUNCE_MS)
}

/** 429 指數退避：30s → 60s → 120s（上限），退避結束後重試單次 */
function scheduleBackoff(): void {
  backoff = backoff === 0 ? BACKOFF_BASE_MS : Math.min(backoff * 2, BACKOFF_MAX_MS)
  clearBackoffTimer()
  backoffTimer = window.setTimeout(() => {
    backoffTimer = undefined
    void syncOnce()
  }, backoff)
}

/** 前景輪詢：每 60s，僅頁面可見時執行 */
function startPolling(): void {
  stopPolling()
  if (!syncActive.value) return
  pollTimer = window.setInterval(() => {
    if (isVisible()) void syncOnce()
  }, POLL_INTERVAL_MS)
}

function stopPolling(): void {
  if (pollTimer !== undefined) {
    clearInterval(pollTimer)
    pollTimer = undefined
  }
}

/** visibilitychange(visible) / window focus → 立即同步 */
function onVisibility(): void {
  if (isVisible()) void syncOnce()
}

function ensureListeners(): void {
  if (listenersRegistered) return
  listenersRegistered = true
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('focus', onVisibility)
}

function removeListeners(): void {
  if (!listenersRegistered) return
  listenersRegistered = false
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('focus', onVisibility)
}

// ── 透過 Worker 建立帳號（§2.1）──

/**
 * createAccount — 輸入 email → 透過 Cloudflare Worker 建立 kvdb bucket + 取得 token
 *
 * Worker 回傳 { access_token, bucket_id }：
 * - access_token 存入 localStorage → 啟動同步
 * - bucket_id 存入 localStorage（供未來多 bucket 擴充）
 */
async function createAccount(email: string): Promise<void> {
  if (!email.trim()) return
  status.value = 'syncing'
  lastError.value = null
  try {
    const res = await fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim() }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }))
      throw new Error(body.error || `建立帳號失敗: ${res.status}`)
    }
    const { access_token, bucket_id } = await res.json() as { access_token: string; bucket_id: string }
    if (!access_token) throw new Error('Worker 未回傳 access_token')

    // 存入 localStorage
    try {
      localStorage.setItem(TOKEN_KEY, access_token)
      if (bucket_id) {
        localStorage.setItem('stockpayday-sync-bucket-id', bucket_id)
      }
    } catch {
      // localStorage 不可用 → 視同未配對
      token.value = ''
      syncActiveRef.value = false
      status.value = 'disabled'
      lastError.value = '無法儲存同步金鑰（localStorage 不可用）'
      return
    }

    token.value = access_token
    syncActiveRef.value = true
    ensureListeners()
    startPolling()
    void syncOnce()
  } catch (err) {
    lastError.value = err instanceof Error ? err.message : '建立帳號失敗'
    status.value = 'error'
  }
}

// ── 對外 API（配對 / 停用）──

function setToken(value: string): void {
  const trimmed = value.trim()
  if (trimmed) {
    try {
      localStorage.setItem(TOKEN_KEY, trimmed)
    } catch {
      // localStorage 不可用 → 視同未配對，同步不啟動（維持現況）
      token.value = ''
      syncActiveRef.value = false
      status.value = 'disabled'
      return
    }
  } else {
    try {
      localStorage.removeItem(TOKEN_KEY)
    } catch {
      // ignore
    }
  }

  token.value = trimmed
  syncActiveRef.value = syncActive.value // 同步驅動 useWatchlist 的墓碑語意
  if (syncActive.value) {
    status.value = 'syncing'
    ensureListeners()
    startPolling()
    void syncOnce()
  } else {
    stopPolling()
    removeListeners()
  }
}

function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // ignore
  }
  token.value = ''
  syncActiveRef.value = false
  status.value = 'disabled'
  lastError.value = null
  backoff = 0
  stopPolling()
  removeListeners()
  clearDebounceTimer()
  clearBackoffTimer()
}

// ── 初始化：有配對碼才啟動（reload 恢復配對）──
syncActiveRef.value = syncActive.value
if (syncActive.value) {
  ensureListeners()
  startPolling()
  void syncOnce()
}

// 本地變更 → debounce 寫回（$1.4 watchEffect；快照比對防自觸發）
watchEffect(() => {
  if (!syncActive.value) return
  const { items } = useWatchlist()
  // 深度追蹤 items 內容：add() 的 push / 墓碑寫入等原地變更亦能觸發 debounce
  void JSON.stringify(items.value)
  scheduleDebouncedSync()
})

// ── cleanup（組件 unmount 時清除 timer/listener）──
function cleanup(): void {
  stopPolling()
  removeListeners()
  clearDebounceTimer()
  clearBackoffTimer()
}

export function useWatchlistSync() {
  const instance = getCurrentInstance()
  if (instance) {
    onBeforeUnmount(cleanup)
  }
  // 組件重新掛載且仍已配對但引擎已停止（例如被其他實例 unmount 清理）→ 恢復輪詢
  if (syncActive.value && pollTimer === undefined) {
    ensureListeners()
    startPolling()
  }
  return { token, status, lastSyncedAt, lastError, syncActive, createAccount, setToken, clearToken, syncOnce }
}

/** 測試用：重置引擎 module 狀態（token/計時器/監聽器/快照） */
export function resetSyncState(): void {
  clearDebounceTimer()
  clearBackoffTimer()
  stopPolling()
  removeListeners()
  backoff = 0
  inFlight = false
  lastPushedSnapshot = null
  token.value = ''
  status.value = 'disabled'
  lastSyncedAt.value = null
  lastError.value = null
  syncActiveRef.value = false
}