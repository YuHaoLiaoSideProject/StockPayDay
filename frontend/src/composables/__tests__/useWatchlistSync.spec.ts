/**
 * useWatchlistSync 單元測試（Phase 9 同步引擎）
 *
 * 對應測試計畫 F- 群組：merge 並集/LWW/墓碑、429 退避（fake timers）、
 * 未配對零請求、kvdb fetch mock（URL/body/429）、setToken/clearToken 對
 * syncActiveRef 的影響、debounce/輪詢/前景可見性、初始化 reload 恢復。
 *
 * 架構更新：移除 Cloudflare Worker，前端直連 kvdb.io。
 * - 建 bucket：POST https://kvdb.io/ with form body email=xxx → 純文字 bucket_id
 * - 同步讀寫：GET/POST https://kvdb.io/{bucket_id}/user:me:watchlist
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick, defineComponent } from 'vue'
import { mount } from '@vue/test-utils'
import type { WatchlistItem, WatchlistSyncDoc } from '../../types/watchlist'
import { useWatchlist, syncActiveRef } from '../useWatchlist'
import { useWatchlistSync, merge, resetSyncState } from '../useWatchlistSync'

/** 快速製造 WatchlistItem（測試用） */
function item(code: string, opts: Partial<WatchlistItem> = {}): WatchlistItem {
  return { code, name: `${code} 名稱`, type: 'stock', addedAt: 100, ...opts }
}

/**
 * kvdb.io fetch mock：可在測試中途切換行為（404/429/fail/401/500/POST 特定狀態）
 * - mode 'ok' + store null → GET 404（首次配對語意）
 * - mode 'ok' + store 有值 → GET 200 回傳 store
 * - POST https://kvdb.io/（建 bucket）→ 回傳純文字 bucket_id
 * - 一律記錄 calls（url / method / parsed body）
 */
type MockMode = 'ok' | '404' | '429' | 'fail' | 'unauthorized' | 'server-error'

interface KvdbCall {
  url: string
  method: string
  body?: WatchlistSyncDoc
  status: number
}

interface KvdbMockState {
  mode: MockMode
  store: WatchlistSyncDoc | null
  /** 若設定，POST 一律回傳此狀態碼（用於測 push 失敗/429） */
  forcePostStatus?: number
  /** 建 bucket 回傳的 bucket_id（預設 'mock-bucket'） */
  createdBucketId?: string
}

function createKvdbMock() {
  const calls: KvdbCall[] = []
  const state: KvdbMockState = { mode: 'ok', store: null }
  const fn = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input)
    const method = (init?.method as string) ?? 'GET'

    // 非 kvdb 請求不記錄、不處理
    if (!url.startsWith('https://kvdb.io')) {
      return { ok: false, status: 404, text: async () => '', json: async () => null }
    }

    if (state.mode === 'fail') throw new TypeError('Failed to fetch')
    if (state.mode === '429') {
      calls.push({ url, method, status: 429 })
      return { ok: false, status: 429, text: async () => 'rate limited', json: async () => null }
    }
    if (state.mode === 'unauthorized') {
      calls.push({ url, method, status: 401 })
      return { ok: false, status: 401, text: async () => 'unauthorized', json: async () => null }
    }
    if (state.mode === 'server-error') {
      calls.push({ url, method, status: 500 })
      return { ok: false, status: 500, text: async () => 'server error', json: async () => null }
    }

    // 建 bucket：POST https://kvdb.io/（無 bucket_id 在路徑中）
    // 注意：happy-dom 的 fetch 可能不會正規化 URL（不加 trailing slash）
    if (method === 'POST' && (url === 'https://kvdb.io/' || url === 'https://kvdb.io')) {
      const bucketId = state.createdBucketId ?? 'mock-bucket'
      calls.push({ url, method, status: 200 })
      return { ok: true, status: 200, text: async () => bucketId, json: async () => null }
    }

    // 同步寫入：POST https://kvdb.io/{bucket_id}/...
    if (method === 'POST') {
      const forced = state.forcePostStatus
      if (forced !== undefined) {
        calls.push({ url, method, status: forced })
        return { ok: forced >= 200 && forced < 300, status: forced, text: async () => '', json: async () => null }
      }
      const body = init?.body ? (JSON.parse(init.body as string) as WatchlistSyncDoc) : undefined
      state.store = body ?? null
      calls.push({ url, method, body, status: 200 })
      return { ok: true, status: 200, text: async () => '', json: async () => null }
    }

    // 同步讀取：GET https://kvdb.io/{bucket_id}/...
    if (state.mode === '404' || state.store === null) {
      calls.push({ url, method, status: 404 })
      return { ok: false, status: 404, text: async () => '', json: async () => null }
    }
    calls.push({ url, method, status: 200 })
    return { ok: true, status: 200, text: async () => '', json: async () => state.store }
  })
  return { fn, calls, state }
}

type KvdbMock = ReturnType<typeof createKvdbMock>

/** 清空與重設全模組狀態（每次測試前） */
function resetAll(): void {
  localStorage.clear()
  resetSyncState()
  useWatchlist().reset()
  vi.unstubAllGlobals()
}

/** 繳出微任務（Vue scheduler / async chain），輪數足夠即穩定 */
async function flushMicrotasks(times = 40): Promise<void> {
  for (let i = 0; i < times; i++) await Promise.resolve()
}

/** 控制 document.visibilityState（happy-dom 以定義實例屬性覆寫原型 getter） */
function setVisibility(state: 'visible' | 'hidden'): void {
  Object.defineProperty(document, 'visibilityState', { value: state, configurable: true })
}

const BUCKET_ID_KEY = 'stockpayday-sync-bucket-id'
const KVDB_URL_BASE = 'https://kvdb.io'

// ============================================================
// merge 合併規則（F-04 / F-11b / F-12 / F-27b）
// ============================================================
describe('merge 合併規則', () => {
  it('F-04 合併為並集：兩端各自獨有的項目皆保留', () => {
    const local = [item('2330', { addedAt: 100 })]
    const remote = [item('0050', { addedAt: 200 })]

    const result = merge(local, remote)

    expect(result.map(i => i.code).sort()).toEqual(['0050', '2330'])
    expect(result).toHaveLength(2)
  })

  it('F-12 同股雙端變更以最後寫入者勝出（本地較新）', () => {
    const local = [item('X', { name: '本地版', addedAt: 50, updatedAt: 200 })]
    const remote = [item('X', { name: '雲端版', addedAt: 50, updatedAt: 100 })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('本地版')
    expect(result[0].updatedAt).toBe(200)
  })

  it('同股雙端變更以最後寫入者勝出（雲端較新）', () => {
    const local = [item('X', { name: '本地版', addedAt: 50, updatedAt: 100 })]
    const remote = [item('X', { name: '雲端版', addedAt: 50, updatedAt: 200 })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('雲端版')
    expect(result[0].updatedAt).toBe(200)
  })

  it('F-11b 墓碑為最終狀態：較新墓碑不被本地舊活躍資料覆蓋', () => {
    const local = [item('X', { addedAt: 50, updatedAt: 100 })] // 舊的活躍項目
    const remote = [item('X', { addedAt: 50, updatedAt: 300, deleted: true })] // 較新墓碑

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBe(true)
  })

  it('BDD Scenario 12 較新活躍項目勝過較早墓碑（重新追蹤）', () => {
    const local = [item('X', { addedAt: 55, updatedAt: 200 })] // 較晚重新加入
    const remote = [item('X', { addedAt: 50, updatedAt: 100, deleted: true })] // 較早墓碑

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBeUndefined()
    expect(result[0].updatedAt).toBe(200)
  })

  it('同刻比對：墓碑（deleted）為最終狀態勝出', () => {
    const local = [item('X', { addedAt: 100, updatedAt: 100 })]
    const remote = [item('X', { addedAt: 100, updatedAt: 100, deleted: true })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBe(true)
  })

  it('F-27b 舊資料無 updatedAt 以 addedAt 比對（採用雲端較新者）', () => {
    const local = [item('X', { addedAt: 100, updatedAt: 100 })]
    const remote = [item('X', { addedAt: 300 })] // 無 updatedAt 的舊資料

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].addedAt).toBe(300)
    expect(result[0].updatedAt).toBeUndefined()
  })

  it('墓碑保留在陣列中（removed 的 code 仍存在於合併結果）', () => {
    const local = [item('2330', { addedAt: 100 })]
    const remote = [item('0056', { addedAt: 100, updatedAt: 200, deleted: true })]

    const result = merge(local, remote)

    expect(result.map(i => i.code).sort()).toEqual(['0056', '2330'])
    expect(result.find(i => i.code === '0056')?.deleted).toBe(true)
  })
})

// ============================================================
// createAccount（直連 kvdb.io 建立 bucket）
// ============================================================
describe('createAccount（直連 kvdb.io）', () => {
  let kvdb: KvdbMock

  beforeEach(() => {
    resetAll()
    kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('POST kvdb.io/ → 回傳 bucket_id、存入 localStorage、不啟動同步', async () => {
    kvdb.state.createdBucketId = 'new-bucket-abc'
    const sync = useWatchlistSync()
    const result = await sync.createAccount('user@example.com')

    // POST https://kvdb.io/（建 bucket）
    const createCalls = kvdb.calls.filter(c => (c.url === 'https://kvdb.io/' || c.url === 'https://kvdb.io') && c.method === 'POST')
    expect(createCalls).toHaveLength(1)

    expect(result.bucketId).toBe('new-bucket-abc')
    expect(localStorage.getItem(BUCKET_ID_KEY)).toBe('new-bucket-abc')

    // 建 bucket 後不設 bucketId、不啟動同步（等待 email 驗證）
    expect(sync.bucketId.value).toBe('') // 尚未 confirmVerification
    expect(sync.syncActive.value).toBe(false)
    // 沒有發起任何同步請求
    const syncCalls = kvdb.calls.filter(c => c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')
    expect(syncCalls).toHaveLength(0)
  })

  it('POST kvdb.io/ 失敗 → status=error、lastError 含錯誤訊息、bucket_id 未寫入', async () => {
    kvdb.state.mode = 'server-error'
    const sync = useWatchlistSync()

    await expect(sync.createAccount('user@example.com')).rejects.toThrow()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toContain('建立帳號失敗')
    expect(sync.bucketId.value).toBe('')
    expect(localStorage.getItem(BUCKET_ID_KEY)).toBeNull()
  })

  it('POST kvdb.io/ 網路失敗 → lastError=建立帳號失敗、本地不受影響', async () => {
    kvdb.state.mode = 'fail'
    const { add } = useWatchlist()
    add('2330', '台積電')

    const sync = useWatchlistSync()
    await expect(sync.createAccount('user@example.com')).rejects.toThrow()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('Failed to fetch')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('空白 email → 不發任何請求、不改變狀態', async () => {
    const sync = useWatchlistSync()
    await expect(sync.createAccount('   ')).rejects.toThrow()

    expect(kvdb.calls).toHaveLength(0)
    expect(sync.status.value).toBe('disabled')
  })

  it('kvdb.io 未回傳 bucket_id → lastError 含錯誤', async () => {
    kvdb.state.createdBucketId = ''
    const sync = useWatchlistSync()

    await expect(sync.createAccount('user@example.com')).rejects.toThrow()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toContain('未回傳 bucket_id')
  })

  it('回傳值含 bucketId', async () => {
    kvdb.state.createdBucketId = 'test-123'
    const sync = useWatchlistSync()
    const result = await sync.createAccount('user@example.com')
    expect(result).toEqual({ bucketId: 'test-123' })
  })
})

// ============================================================
// confirmVerification（驗證後啟動同步）
// ============================================================
describe('confirmVerification', () => {
  let kvdb: KvdbMock

  beforeEach(() => {
    resetAll()
    kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('confirmVerification 啟動同步：syncActiveRef=true、發起 pull + push', async () => {
    kvdb.state.createdBucketId = 'verify-bucket'
    const sync = useWatchlistSync()
    await sync.createAccount('user@example.com')

    // 建 bucket 後無同步請求
    expect(kvdb.calls.filter(c => c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')).toHaveLength(0)

    // 確認驗證 → 啟動同步
    sync.confirmVerification()
    await flushMicrotasks()

    expect(syncActiveRef.value).toBe(true)
    expect(sync.status.value).toBe('synced')
    // 發起 pull（GET 404）+ push（POST）
    const syncCalls = kvdb.calls.filter(c => c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')
    expect(syncCalls.length).toBeGreaterThanOrEqual(2)
  })

  it('confirmVerification 在未建立 bucket 時不執行', () => {
    const sync = useWatchlistSync()
    sync.confirmVerification() // 無 bucket_id，不應崩潰
    expect(syncActiveRef.value).toBe(false)
  })
})

// ============================================================
// syncActive 語意 / setToken / clearToken（需求 2、7）
// ============================================================
describe('syncActive 語意與對外 API', () => {
  let kvdb: KvdbMock

  beforeEach(() => {
    resetAll()
    kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('無 token → syncActive=false，syncOnce 直接 return（零請求）', async () => {
    const sync = useWatchlistSync()
    expect(sync.syncActive.value).toBe(false)
    expect(sync.status.value).toBe('disabled')

    await sync.syncOnce()

    expect(kvdb.fn).not.toHaveBeenCalled()
    expect(sync.status.value).toBe('disabled')
  })

  it('對外 API 形狀：回傳 { bucketId, status, lastSyncedAt, lastError, syncActive, createAccount, confirmVerification, setToken, clearToken, syncOnce }', () => {
    const sync = useWatchlistSync()
    expect(Object.keys(sync)).toEqual([
      'bucketId',
      'status',
      'lastSyncedAt',
      'lastError',
      'syncActive',
      'createAccount',
      'confirmVerification',
      'setToken',
      'clearToken',
      'syncOnce',
    ])
  })

  it('F-01 setToken 寫入 localStorage、啟動同步並讓 syncActiveRef 為 true', async () => {
    const sync = useWatchlistSync()
    sync.setToken('  my-bucket-123  ')

    expect(sync.bucketId.value).toBe('my-bucket-123')
    expect(localStorage.getItem(BUCKET_ID_KEY)).toBe('my-bucket-123')
    expect(sync.syncActive.value).toBe(true)
    expect(syncActiveRef.value).toBe(true) // useWatchlist 的墓碑語意旗標被同步
    expect(sync.status.value).toBe('syncing')

    await flushMicrotasks()

    expect(sync.status.value).toBe('synced')
    expect(sync.lastSyncedAt.value).toBeTypeOf('number')
    expect(sync.lastError.value).toBeNull()
  })

  it('F-19 clearToken 清除 token、停用同步、syncActiveRef 回 false 且本地清單保留', async () => {
    const { add, items } = useWatchlist()
    add('2330', '台積電', 'stock')

    const sync = useWatchlistSync()
    sync.setToken('tok')

    expect(syncActiveRef.value).toBe(true)

    sync.clearToken()

    expect(sync.bucketId.value).toBe('')
    expect(localStorage.getItem(BUCKET_ID_KEY)).toBeNull()
    expect(sync.syncActive.value).toBe(false)
    expect(syncActiveRef.value).toBe(false)
    expect(sync.status.value).toBe('disabled')
    // 停用同步後本地清單保留
    expect(items.value.map(i => i.code)).toContain('2330')
  })

  it('setToken 空字串（含空白）→ 不啟動、不發請求', async () => {
    const sync = useWatchlistSync()
    sync.setToken('   ')

    expect(sync.syncActive.value).toBe(false)
    expect(syncActiveRef.value).toBe(false)
    expect(sync.status.value).toBe('disabled')
    expect(kvdb.fn).not.toHaveBeenCalled()
  })

  it('F-26 localStorage 不可用（setItem 拋錯）→ 視同未配對，同步不啟動', async () => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = () => {
      throw new Error('quota exceeded')
    }
    try {
      const sync = useWatchlistSync()
      sync.setToken('tok')

      expect(sync.bucketId.value).toBe('')
      expect(sync.syncActive.value).toBe(false)
      expect(syncActiveRef.value).toBe(false)
      expect(sync.status.value).toBe('disabled')
      expect(kvdb.fn).not.toHaveBeenCalled()
      // 追蹤清單既有操作維持正常
      const { add, isWatched } = useWatchlist()
      add('2330', '台積電')
      expect(isWatched('2330')).toBe(true)
    } finally {
      Storage.prototype.setItem = original
    }
  })

  it('syncActive 下 remove 走墓碑語意（syncActiveRef 生效）', () => {
    const { add, remove, items } = useWatchlist()
    const sync = useWatchlistSync()
    sync.setToken('tok')

    add('2330', '台積電', 'stock')
    remove('2330')

    expect(items.value[0].deleted).toBe(true)
    expect(items.value).toHaveLength(1)
  })
})

// ============================================================
// kvdb.io 契約（F-03 / F-09 / F-14 / F-24 / F-20）
// ============================================================
describe('kvdb.io 讀寫契約', () => {
  let kvdb: KvdbMock

  beforeEach(() => {
    resetAll()
    kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('F-03 首次配對：GET 404 → merge 本地 → POST 建立雲端文件', async () => {
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')
    add('0050', '元大台灣50', 'etf')

    const sync = useWatchlistSync()
    sync.setToken('first-token')
    await flushMicrotasks()

    // GET 404（首次）→ 無 POST 前先 GET
    expect(kvdb.calls[0].method).toBe('GET')
    expect(kvdb.calls[0].status).toBe(404)
    expect(kvdb.calls[0].url).toBe('https://kvdb.io/first-token/user:me:watchlist')

    // POST 建立含本地 items 的 doc
    expect(kvdb.calls[1].method).toBe('POST')
    expect(kvdb.calls[1].url).toBe('https://kvdb.io/first-token/user:me:watchlist')
    expect(kvdb.calls[1].status).toBe(200)
    const posted = kvdb.calls[1].body!
    expect(posted.updatedAt).toBeTypeOf('number')
    expect(posted.items.map(i => i.code).sort()).toEqual(['0050', '2330'])

    expect(sync.status.value).toBe('synced')
    expect(sync.lastSyncedAt.value).toBeTypeOf('number')
    // 本機清單內容不變
    expect(useWatchlist().items.value.map(i => i.code).sort()).toEqual(['0050', '2330'])
  })

  it('POST 使用 application/json header 並回傳 WatchlistSyncDoc body', async () => {
    useWatchlist().add('2330', '台積電')
    const sync = useWatchlistSync()
    sync.setToken('tok')
    await flushMicrotasks()

    const postCall = kvdb.fn.mock.calls[1]
    expect(postCall[1]).toMatchObject({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const doc = JSON.parse(postCall[1]!.body as string) as WatchlistSyncDoc
    expect(typeof doc.updatedAt).toBe('number')
    expect(doc.items[0].code).toBe('2330')
  })

  it('F-09 雲端較新：synceOnce 合併後本地收到遠端新增項目', async () => {
    kvdb.state.store = {
      updatedAt: 500,
      items: [
        item('2330', { addedAt: 100, updatedAt: 100 }),
        item('0056', { addedAt: 300, updatedAt: 300 }),
      ],
    }
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const sync = useWatchlistSync()
    sync.setToken('tok')
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code).sort()
    expect(codes).toEqual(['0056', '2330']) // 並集：本地 2330 + 遠端 0056
    expect(sync.status.value).toBe('synced')
    // 合併結果（含遠端較新資料）已寫回雲端
    expect(kvdb.state.store?.items.map(i => i.code).sort()).toEqual(['0056', '2330'])
  })

  it('F-24 配對碼無效（401）：同步失敗、本地不受影響', async () => {
    kvdb.state.mode = 'unauthorized'
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const sync = useWatchlistSync()
    sync.setToken('invalid-token')
    await flushMicrotasks()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('pull failed: 401')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('push 非 OK（500）：lastError 為 push failed', async () => {
    kvdb.state.forcePostStatus = 500
    useWatchlist().add('2330', '台積電')

    const sync = useWatchlistSync()
    sync.setToken('tok')
    await flushMicrotasks()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('push failed: 500')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('F-14 離線（fetch 網路錯誤）：同步失敗、本地清單完整保留', async () => {
    kvdb.state.mode = 'fail'
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const sync = useWatchlistSync()
    sync.setToken('tok')
    await flushMicrotasks()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('Failed to fetch')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('F-20 停用後重新啟用：與雲端既有清單合併為並集', async () => {
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const sync = useWatchlistSync()
    sync.setToken('old-token')
    await flushMicrotasks()
    sync.clearToken()
    expect(sync.syncActive.value).toBe(false)

    // 雲端此時已有另一裝置寫入的 0050
    kvdb.state.store = {
      updatedAt: 999,
      items: [
        item('2330', { addedAt: 100, updatedAt: 100 }),
        item('0050', { addedAt: 400, updatedAt: 400 }),
      ],
    }

    sync.setToken('new-token')
    expect(sync.status.value).toBe('syncing')
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code).sort()
    expect(codes).toEqual(['0050', '2330'])
    expect(sync.status.value).toBe('synced')
  })
})

// ============================================================
// debounce / 輪詢 / 退避 / 前景可見性 / 防死循環（fake timers）
// ============================================================
describe('同步觸發策略（debounce / 輪詢 / 429 退避）', () => {
  let kvdb: KvdbMock
  let sync: ReturnType<typeof useWatchlistSync>

  beforeEach(() => {
    resetAll()
    kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'] })
    setVisibility('visible')
    sync = useWatchlistSync()
    // 建立已配對 + 首次同步完成的 baseline（GET 404 → POST 建立，共 2 次 fetch）
    sync.setToken('tok')
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
    setVisibility('visible')
    resetAll()
  })

  async function settleBaseline(): Promise<void> {
    await vi.advanceTimersByTimeAsync(0)
    await flushMicrotasks()
    expect(kvdb.fn).toHaveBeenCalledTimes(2)
    expect(sync.status.value).toBe('synced')
  }

  it('F-08 本地變更 debounce 1.5s 後寫回；未滿 1.5s 前不觸發', async () => {
    await settleBaseline()

    useWatchlist().add('X', '測試股')
    await nextTick() // flush watchEffect → 排程 debounce

    // 未滿 1.5s：不發任何請求
    await vi.advanceTimersByTimeAsync(1_400)
    expect(kvdb.fn).toHaveBeenCalledTimes(2)

    // 滿 1.5s：觸發一次 syncOnce（GET + POST 寫回）
    await vi.advanceTimersByTimeAsync(100)
    expect(kvdb.fn).toHaveBeenCalledTimes(4)
    const lastPost = [...kvdb.calls].reverse().find(c => c.method === 'POST' && c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')!
    expect(lastPost.body?.items.some(i => i.code === 'X')).toBe(true)
  })

  it('F-10 前台每 60 秒自動檢查一次（僅 visible）', async () => {
    await settleBaseline()

    await vi.advanceTimersByTimeAsync(60_000)
    expect(kvdb.fn).toHaveBeenCalledTimes(4) // GET + POST

    await vi.advanceTimersByTimeAsync(60_000)
    expect(kvdb.fn).toHaveBeenCalledTimes(6)
  })

  it('F-18 背景不輪詢；回前景（visibilitychange）立即同步一次', async () => {
    await settleBaseline()

    setVisibility('hidden')
    await vi.advanceTimersByTimeAsync(120_000)
    expect(kvdb.fn).toHaveBeenCalledTimes(2) // 背景期間零請求

    setVisibility('visible')
    document.dispatchEvent(new Event('visibilitychange'))
    await flushMicrotasks()

    expect(kvdb.fn).toHaveBeenCalledTimes(4) // 回前景立即同步
  })

  it('window focus → 立即同步一次', async () => {
    await settleBaseline()

    window.dispatchEvent(new Event('focus'))
    await flushMicrotasks()

    expect(kvdb.fn).toHaveBeenCalledTimes(4)
  })

  it('F-17a/b/c 連續 429 退避：30s → 60s → 120s（指數遞增、上限 120s）', async () => {
    await settleBaseline()

    kvdb.state.mode = '429'

    await sync.syncOnce()
    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('速率限制（429），30 秒後重試')

    await sync.syncOnce()
    expect(sync.lastError.value).toBe('速率限制（429），60 秒後重試')

    await sync.syncOnce()
    expect(sync.lastError.value).toBe('速率限制（429），120 秒後重試')

    await sync.syncOnce()
    expect(sync.lastError.value).toBe('速率限制（429），120 秒後重試') // 上限不超過 120s
  })

  it('F-16 429 退避結束後自動重試單次成功 → synced、退避歸零', async () => {
    await settleBaseline()

    kvdb.state.mode = '429'
    await sync.syncOnce()
    expect(sync.lastError.value).toBe('速率限制（429），30 秒後重試')

    // 恢復正常後，快轉 30s → 退避 timer 自動重試一次
    kvdb.state.mode = 'ok'
    await vi.advanceTimersByTimeAsync(30_000)
    await flushMicrotasks()

    expect(sync.status.value).toBe('synced')
    expect(sync.lastError.value).toBeNull()

    // 退避已歸零：再遇 429 從 30s 開始
    kvdb.state.mode = '429'
    await sync.syncOnce()
    expect(sync.lastError.value).toBe('速率限制（429），30 秒後重試')
  })

  it('push 也處理 429（POST 429 → 退避排程）', async () => {
    await settleBaseline()

    kvdb.state.forcePostStatus = 429
    await sync.syncOnce()

    expect(sync.status.value).toBe('error')
    expect(sync.lastError.value).toBe('速率限制（429），30 秒後重試')
  })

  it('F-15 離線期間變更保留，恢復連線後自動合併（含遠端新增）', async () => {
    await settleBaseline()

    // 離線：加入 X（雲端已有另一裝置寫入的 Y）
    kvdb.state.mode = 'fail'
    useWatchlist().add('X', '離線加入')
    await nextTick()
    await vi.advanceTimersByTimeAsync(1_500)
    await flushMicrotasks()

    expect(sync.status.value).toBe('error')
    expect(useWatchlist().items.value.some(i => i.code === 'X')).toBe(true) // 本地保留

    // 恢復連線；雲端此時有 Y
    kvdb.state.store = {
      updatedAt: 999,
      items: [item('Y', { addedAt: 700, updatedAt: 700 })],
    }
    kvdb.state.mode = 'ok'
    document.dispatchEvent(new Event('visibilitychange')) // 切回前景 → 立即同步
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code)
    expect(codes).toContain('X') // 離線變更保留
    expect(codes).toContain('Y') // 遠端變更併入
    expect(sync.status.value).toBe('synced')
  })

  it('需求 8：同步寫入後無實際變更不重複推（不觸發自身 watchEffect 死循環）', async () => {
    await settleBaseline()

    // 手動再同步一輪（無任何本地變更）
    await sync.syncOnce()
    await flushMicrotasks()
    expect(kvdb.fn).toHaveBeenCalledTimes(4)

    // 等過 debounce 與額外時間：不應有自觸發的額外請求
    await vi.advanceTimersByTimeAsync(1_500)
    await vi.advanceTimersByTimeAsync(5_000)
    expect(kvdb.fn).toHaveBeenCalledTimes(4)

    // 對照組：本地真實變更 → 正好一輪新請求（GET + POST）
    useWatchlist().add('Z', '本機新增')
    await nextTick()
    await vi.advanceTimersByTimeAsync(1_500)
    await flushMicrotasks()
    expect(kvdb.fn).toHaveBeenCalledTimes(6)
    const lastPost = [...kvdb.calls].reverse().find(c => c.method === 'POST' && c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')!
    expect(lastPost.body?.items.some(i => i.code === 'Z')).toBe(true)
  })

  it('需求 6：組件 unmount 時清除輪詢與監聽器（onBeforeUnmount 清理）', async () => {
    await settleBaseline()

    const Comp = defineComponent({
      setup() {
        useWatchlistSync()
        return {}
      },
      template: '<div />',
    })
    const wrapper = mount(Comp)
    await flushMicrotasks()

    const before = kvdb.fn.mock.calls.length
    wrapper.unmount() // cleanup：stopPolling + removeListeners + clear timers

    setVisibility('visible')
    await vi.advanceTimersByTimeAsync(120_000) // 若輪詢未停止會 +2
    document.dispatchEvent(new Event('visibilitychange')) // 若監聽器未移除會 +2
    window.dispatchEvent(new Event('focus'))

    expect(kvdb.fn.mock.calls.length).toBe(before)
  })
})

// ============================================================
// 初始化 reload 恢復配對（以 resetModules 重建模組模擬重新載入）
// ============================================================
describe('初始化：reload 恢復配對（module init）', () => {
  beforeEach(() => {
    vi.useRealTimers()
    localStorage.clear()
    vi.unstubAllGlobals()
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
    setVisibility('visible')
  })

  it('F-01 reload：頁面載入讀取 localStorage token 並自動執行首次同步（syncActiveRef=true）', async () => {
    localStorage.setItem(BUCKET_ID_KEY, 'reload-token')
    localStorage.setItem(
      'stockpayday-watchlist',
      JSON.stringify([{ code: '2330', name: '台積電', type: 'stock', addedAt: 1000, updatedAt: 1000 }]),
    )

    const kvdb = createKvdbMock()
    vi.stubGlobal('fetch', kvdb.fn)

    const wl = await import('../useWatchlist')
    const syncMod = await import('../useWatchlistSync')

    await vi.waitFor(() => expect(kvdb.calls.length).toBe(2))

    const sync = syncMod.useWatchlistSync()
    expect(sync.bucketId.value).toBe('reload-token')
    expect(sync.syncActive.value).toBe(true)
    expect(wl.syncActiveRef.value).toBe(true) // 初始化同步 syncActiveRef
    expect(sync.status.value).toBe('synced')

    // GET 404 → POST 建立（含 localStorage 載入的本地清單）
    expect(kvdb.calls[0].url).toBe('https://kvdb.io/reload-token/user:me:watchlist')
    const post = kvdb.calls.find(c => c.method === 'POST' && c.url !== 'https://kvdb.io/' && c.url !== 'https://kvdb.io')!
    expect(post.body?.items.some(i => i.code === '2330')).toBe(true)

    syncMod.resetSyncState() // 清理 fresh module 的 timer/listener
  })

  it('F-26 localStorage 不可用（getItem 拋錯）→ 視同未配對、同步引擎不啟動', async () => {
    localStorage.setItem(BUCKET_ID_KEY, 'tok')
    const original = Storage.prototype.getItem
    Storage.prototype.getItem = () => {
      throw new Error('access denied')
    }
    try {
      const kvdb = createKvdbMock()
      vi.stubGlobal('fetch', kvdb.fn)

      await import('../useWatchlist')
      const syncMod = await import('../useWatchlistSync')

      const sync = syncMod.useWatchlistSync()
      expect(sync.bucketId.value).toBe('')
      expect(sync.syncActive.value).toBe(false)
      expect(sync.status.value).toBe('disabled')
      await sync.syncOnce()
      expect(kvdb.calls).toHaveLength(0) // 視同未配對：不發任何 kvdb 請求

      // 追蹤清單既有操作正常（初始化回退空清單）
      const wl = (await import('../useWatchlist')).useWatchlist()
      wl.add('2330', '台積電')
      expect(wl.isWatched('2330')).toBe(true)

      syncMod.resetSyncState()
    } finally {
      Storage.prototype.getItem = original
    }
  })
})
