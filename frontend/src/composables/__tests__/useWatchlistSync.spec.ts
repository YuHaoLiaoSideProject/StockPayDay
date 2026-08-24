/**
 * useWatchlistSync 單元測試（Phase 9 同步引擎）
 *
 * 對應測試計畫 F- 群組：merge 並集/LWW/墓碑、429 退避（fake timers）、
 * 未配對零請求、npoint.io fetch mock（URL/body/429）、setToken/clearToken 對
 * syncActiveRef 的影響、debounce/輪詢/前景可見性、初始化 reload 恢復。
 *
 * 架構更新：使用 npoint.io 作為後端服務。
 * - 建立空間：POST https://www.npoint.io/documents → 回傳 { token, api_url, ... }
 * - 同步讀寫：GET/POST https://api.npoint.io/{token}
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
 * npoint.io fetch mock：可在測試中途切換行為（404/429/fail/401/500/POST 特定狀態）
 * - mode 'ok' + store null → GET 404（首次配對語意）
 * - mode 'ok' + store 有值 → GET 200 回傳 store
 * - POST https://www.npoint.io/documents（建立空間）→ 回傳 { token: 'xxx' }
 * - POST https://api.npoint.io/{token}（同步寫入）→ 回傳 200
 * - 一律記錄 calls（url / method / parsed body）
 */
type MockMode = 'ok' | '404' | '429' | 'fail' | 'unauthorized' | 'server-error'

interface SyncCall {
  url: string
  method: string
  body?: WatchlistSyncDoc
  status: number
}

interface SyncMockState {
  mode: MockMode
  store: WatchlistSyncDoc | null
  /** 若設定，POST 一律回傳此狀態碼（用於測 push 失敗/429） */
  forcePostStatus?: number
  /** 建立空間回傳的 token（預設 'mock-token'） */
  createdToken?: string
}

function createSyncMock() {
  const calls: SyncCall[] = []
  const state: SyncMockState = { mode: 'ok', store: null }
  const fn = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input)
    const method = (init?.method as string) ?? 'GET'

    // 非 npoint.io 請求不記錄、不處理
    if (!url.includes('npoint.io')) {
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

    // 建立空間：POST https://www.npoint.io/documents
    if (method === 'POST' && url === 'https://www.npoint.io/documents') {
      const token = state.createdToken ?? 'mock-token'
      calls.push({ url, method, status: 200 })
      return { ok: true, status: 200, json: async () => ({ token, api_url: `https://api.npoint.io/${token}` }) }
    }

    // 同步寫入：POST https://api.npoint.io/{token}
    if (method === 'POST' && url.startsWith('https://api.npoint.io/')) {
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

    // 同步讀取：GET https://api.npoint.io/{token}
    if (state.mode === '404' || state.store === null) {
      calls.push({ url, method, status: 404 })
      return { ok: false, status: 404, text: async () => '', json: async () => null }
    }
    calls.push({ url, method, status: 200 })
    return { ok: true, status: 200, text: async () => '', json: async () => state.store }
  })
  return { fn, calls, state }
}

type SyncMock = ReturnType<typeof createSyncMock>

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

const SYNC_TOKEN_KEY = 'stockpayday-sync-token'

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
// createSyncSpace（直連 npoint.io 建立空間）
// ============================================================
describe('createSyncSpace（直連 npoint.io）', () => {
  let sync: SyncMock

  beforeEach(() => {
    resetAll()
    sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('POST npoint.io/documents → 回傳 token、存入 localStorage、不立即啟動同步', async () => {
    sync.state.createdToken = 'new-sync-token-abc'
    const syncApi = useWatchlistSync()
    const result = await syncApi.createAccount()
    await flushMicrotasks()

    // POST https://www.npoint.io/documents（建立空間）
    const createCalls = sync.calls.filter(c => c.url === 'https://www.npoint.io/documents' && c.method === 'POST')
    expect(createCalls).toHaveLength(1)

    expect(result.token).toBe('new-sync-token-abc')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBe('new-sync-token-abc')

    // 建立後不立即啟動同步（等待使用者點擊「開始同步」）
    expect(syncApi.bucketId.value).toBe('') // 尚未啟動
    expect(syncApi.syncActive.value).toBe(false)
    // 沒有發起任何同步請求
    const syncCalls = sync.calls.filter(c => c.url !== 'https://www.npoint.io/documents')
    expect(syncCalls).toHaveLength(0)
  })

  it('POST npoint.io/documents 失敗 → status=error、lastError 含錯誤訊息、token 未寫入', async () => {
    sync.state.mode = 'server-error'
    const syncApi = useWatchlistSync()

    await expect(syncApi.createAccount()).rejects.toThrow()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toContain('建立同步空間失敗')
    expect(syncApi.bucketId.value).toBe('')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBeNull()
  })

  it('POST npoint.io/documents 網路失敗 → lastError=建立同步空間失敗、本地不受影響', async () => {
    sync.state.mode = 'fail'
    const { add } = useWatchlist()
    add('2330', '台積電')

    const syncApi = useWatchlistSync()
    await expect(syncApi.createAccount()).rejects.toThrow()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('Failed to fetch')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('npoint.io 未回傳 token → lastError 含錯誤', async () => {
    sync.state.createdToken = ''
    const syncApi = useWatchlistSync()

    await expect(syncApi.createAccount()).rejects.toThrow()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toContain('未回傳 token')
  })

  it('回傳值含 token', async () => {
    sync.state.createdToken = 'test-123'
    const syncApi = useWatchlistSync()
    const result = await syncApi.createAccount()
    expect(result).toEqual({ token: 'test-123' })
  })
})

// ============================================================
// syncActive 語意 / setToken / clearToken（需求 2、7）
// ============================================================
describe('syncActive 語意與對外 API', () => {
  let sync: SyncMock

  beforeEach(() => {
    resetAll()
    sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('無 token → syncActive=false，syncOnce 直接 return（零請求）', async () => {
    const syncApi = useWatchlistSync()
    expect(syncApi.syncActive.value).toBe(false)
    expect(syncApi.status.value).toBe('disabled')

    await syncApi.syncOnce()

    expect(sync.fn).not.toHaveBeenCalled()
    expect(syncApi.status.value).toBe('disabled')
  })

  it('對外 API 形狀：回傳 { bucketId, status, lastSyncedAt, lastError, syncActive, createAccount, confirmVerification, setToken, clearToken, syncOnce }', () => {
    const syncApi = useWatchlistSync()
    expect(Object.keys(syncApi)).toEqual([
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
    const syncApi = useWatchlistSync()
    syncApi.setToken('  my-sync-token-123  ')

    expect(syncApi.bucketId.value).toBe('my-sync-token-123')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBe('my-sync-token-123')
    expect(syncApi.syncActive.value).toBe(true)
    expect(syncActiveRef.value).toBe(true) // useWatchlist 的墓碑語意旗標被同步
    expect(syncApi.status.value).toBe('syncing')

    await flushMicrotasks()

    expect(syncApi.status.value).toBe('synced')
    expect(syncApi.lastSyncedAt.value).toBeTypeOf('number')
    expect(syncApi.lastError.value).toBeNull()
  })

  it('F-19 clearToken 清除 token、停用同步、syncActiveRef 回 false 且本地清單保留', async () => {
    const { add, items } = useWatchlist()
    add('2330', '台積電', 'stock')

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')

    expect(syncActiveRef.value).toBe(true)

    syncApi.clearToken()

    expect(syncApi.bucketId.value).toBe('')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBeNull()
    expect(syncApi.syncActive.value).toBe(false)
    expect(syncActiveRef.value).toBe(false)
    expect(syncApi.status.value).toBe('disabled')
    // 停用同步後本地清單保留
    expect(items.value.map(i => i.code)).toContain('2330')
  })

  it('setToken 空字串（含空白）→ 不啟動、不發請求', async () => {
    const syncApi = useWatchlistSync()
    syncApi.setToken('   ')

    expect(syncApi.syncActive.value).toBe(false)
    expect(syncActiveRef.value).toBe(false)
    expect(syncApi.status.value).toBe('disabled')
    expect(sync.fn).not.toHaveBeenCalled()
  })

  it('F-26 localStorage 不可用（setItem 拋錯）→ 視同未配對，同步不啟動', async () => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = () => {
      throw new Error('quota exceeded')
    }
    try {
      const syncApi = useWatchlistSync()
      syncApi.setToken('tok')

      expect(syncApi.bucketId.value).toBe('')
      expect(syncApi.syncActive.value).toBe(false)
      expect(syncActiveRef.value).toBe(false)
      expect(syncApi.status.value).toBe('disabled')
      expect(sync.fn).not.toHaveBeenCalled()
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
    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')

    add('2330', '台積電', 'stock')
    remove('2330')

    expect(items.value[0].deleted).toBe(true)
    expect(items.value).toHaveLength(1)
  })
})

// ============================================================
// npoint.io 讀寫契約（F-03 / F-09 / F-14 / F-24 / F-20）
// ============================================================
describe('npoint.io 讀寫契約', () => {
  let sync: SyncMock

  beforeEach(() => {
    resetAll()
    sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)
  })

  afterEach(() => {
    resetAll()
  })

  it('F-03 首次配對：GET 404 → merge 本地 → POST 建立雲端文件', async () => {
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')
    add('0050', '元大台灣50', 'etf')

    const syncApi = useWatchlistSync()
    syncApi.setToken('first-token')
    await flushMicrotasks()

    // GET 404（首次）→ 無 POST 前先 GET
    expect(sync.calls[0].method).toBe('GET')
    expect(sync.calls[0].status).toBe(404)
    expect(sync.calls[0].url).toBe('https://api.npoint.io/first-token')

    // POST 建立含本地 items 的 doc
    expect(sync.calls[1].method).toBe('POST')
    expect(sync.calls[1].url).toBe('https://api.npoint.io/first-token')
    expect(sync.calls[1].status).toBe(200)
    const posted = sync.calls[1].body!
    expect(posted.updatedAt).toBeTypeOf('number')
    expect(posted.items.map(i => i.code).sort()).toEqual(['0050', '2330'])

    expect(syncApi.status.value).toBe('synced')
    expect(syncApi.lastSyncedAt.value).toBeTypeOf('number')
    // 本機清單內容不變
    expect(useWatchlist().items.value.map(i => i.code).sort()).toEqual(['0050', '2330'])
  })

  it('POST 使用 application/json header 並回傳 WatchlistSyncDoc body', async () => {
    useWatchlist().add('2330', '台積電')
    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    const postCall = sync.fn.mock.calls[1]
    expect(postCall[1]).toMatchObject({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    })
    const doc = JSON.parse(postCall[1]!.body as string) as WatchlistSyncDoc
    expect(typeof doc.updatedAt).toBe('number')
    expect(doc.items[0].code).toBe('2330')
  })

  it('F-09 雲端較新：syncOnce 合併後本地收到遠端新增項目', async () => {
    sync.state.store = {
      updatedAt: 500,
      items: [
        item('2330', { addedAt: 100, updatedAt: 100 }),
        item('0056', { addedAt: 300, updatedAt: 300 }),
      ],
    }
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code).sort()
    expect(codes).toEqual(['0056', '2330']) // 並集：本地 2330 + 遠端 0056
    expect(syncApi.status.value).toBe('synced')
    // 合併結果（含遠端較新資料）已寫回雲端
    expect(sync.state.store?.items.map(i => i.code).sort()).toEqual(['0056', '2330'])
  })

  it('F-24 配對碼無效（401）：同步失敗、本地不受影響', async () => {
    sync.state.mode = 'unauthorized'
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const syncApi = useWatchlistSync()
    syncApi.setToken('invalid-token')
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('pull failed: 401')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('push 非 OK（500）：lastError 為 push failed', async () => {
    sync.state.forcePostStatus = 500
    useWatchlist().add('2330', '台積電')

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('push failed: 500')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('F-14 離線（fetch 網路錯誤）：同步失敗、本地清單完整保留', async () => {
    sync.state.mode = 'fail'
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('Failed to fetch')
    expect(useWatchlist().items.value.map(i => i.code)).toContain('2330')
  })

  it('F-20 停用後重新啟用：與雲端既有清單合併為並集', async () => {
    const { add } = useWatchlist()
    add('2330', '台積電', 'stock')

    const syncApi = useWatchlistSync()
    syncApi.setToken('old-token')
    await flushMicrotasks()
    syncApi.clearToken()
    expect(syncApi.syncActive.value).toBe(false)

    // 雲端此時已有另一裝置寫入的 0050
    sync.state.store = {
      updatedAt: 999,
      items: [
        item('2330', { addedAt: 100, updatedAt: 100 }),
        item('0050', { addedAt: 400, updatedAt: 400 }),
      ],
    }

    syncApi.setToken('new-token')
    expect(syncApi.status.value).toBe('syncing')
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code).sort()
    expect(codes).toEqual(['0050', '2330'])
    expect(syncApi.status.value).toBe('synced')
  })
})

// ============================================================
// debounce / 輪詢 / 退避 / 前景可見性 / 防死循環（fake timers）
// ============================================================
describe('同步觸發策略（debounce / 輪詢 / 429 退避）', () => {
  let sync: SyncMock
  let syncApi: ReturnType<typeof useWatchlistSync>

  beforeEach(() => {
    resetAll()
    sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'] })
    setVisibility('visible')
    syncApi = useWatchlistSync()
    // 建立已配對 + 首次同步完成的 baseline（GET 404 → POST 建立，共 2 次 fetch）
    syncApi.setToken('tok')
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
    expect(sync.fn).toHaveBeenCalledTimes(2)
    expect(syncApi.status.value).toBe('synced')
  }

  it('F-08 本地變更 debounce 1.5s 後寫回；未滿 1.5s 前不觸發', async () => {
    await settleBaseline()

    useWatchlist().add('X', '測試股')
    await nextTick() // flush watchEffect → 排程 debounce

    // 未滿 1.5s：不發任何請求
    await vi.advanceTimersByTimeAsync(1_400)
    expect(sync.fn).toHaveBeenCalledTimes(2)

    // 滿 1.5s：觸發一次 syncOnce（GET + POST 寫回）
    await vi.advanceTimersByTimeAsync(100)
    expect(sync.fn).toHaveBeenCalledTimes(4)
    const lastPost = [...sync.calls].reverse().find(c => c.method === 'POST' && c.url !== 'https://www.npoint.io/documents')!
    expect(lastPost.body?.items.some(i => i.code === 'X')).toBe(true)
  })

  it('F-10 前台每 60 秒自動檢查一次（僅 visible）', async () => {
    await settleBaseline()

    await vi.advanceTimersByTimeAsync(60_000)
    expect(sync.fn).toHaveBeenCalledTimes(4) // GET + POST

    await vi.advanceTimersByTimeAsync(60_000)
    expect(sync.fn).toHaveBeenCalledTimes(6)
  })

  it('F-18 背景不輪詢；回前景（visibilitychange）立即同步一次', async () => {
    await settleBaseline()

    setVisibility('hidden')
    await vi.advanceTimersByTimeAsync(120_000)
    expect(sync.fn).toHaveBeenCalledTimes(2) // 背景期間零請求

    setVisibility('visible')
    document.dispatchEvent(new Event('visibilitychange'))
    await flushMicrotasks()

    expect(sync.fn).toHaveBeenCalledTimes(4) // 回前景立即同步
  })

  it('window focus → 立即同步一次', async () => {
    await settleBaseline()

    window.dispatchEvent(new Event('focus'))
    await flushMicrotasks()

    expect(sync.fn).toHaveBeenCalledTimes(4)
  })

  it('F-17a/b/c 連續 429 退避：30s → 60s → 120s（指數遞增、上限 120s）', async () => {
    await settleBaseline()

    sync.state.mode = '429'

    await syncApi.syncOnce()
    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('速率限制（429），30 秒後重試')

    await syncApi.syncOnce()
    expect(syncApi.lastError.value).toBe('速率限制（429），60 秒後重試')

    await syncApi.syncOnce()
    expect(syncApi.lastError.value).toBe('速率限制（429），120 秒後重試')

    await syncApi.syncOnce()
    expect(syncApi.lastError.value).toBe('速率限制（429），120 秒後重試') // 上限不超過 120s
  })

  it('F-16 429 退避結束後自動重試單次成功 → synced、退避歸零', async () => {
    await settleBaseline()

    sync.state.mode = '429'
    await syncApi.syncOnce()
    expect(syncApi.lastError.value).toBe('速率限制（429），30 秒後重試')

    // 恢復正常後，快轉 30s → 退避 timer 自動重試一次
    sync.state.mode = 'ok'
    await vi.advanceTimersByTimeAsync(30_000)
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('synced')
    expect(syncApi.lastError.value).toBeNull()

    // 退避已歸零：再遇 429 從 30s 開始
    sync.state.mode = '429'
    await syncApi.syncOnce()
    expect(syncApi.lastError.value).toBe('速率限制（429），30 秒後重試')
  })

  it('push 也處理 429（POST 429 → 退避排程）', async () => {
    await settleBaseline()

    sync.state.forcePostStatus = 429
    await syncApi.syncOnce()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toBe('速率限制（429），30 秒後重試')
  })

  it('F-15 離線期間變更保留，恢復連線後自動合併（含遠端新增）', async () => {
    await settleBaseline()

    // 離線：加入 X（雲端已有另一裝置寫入的 Y）
    sync.state.mode = 'fail'
    useWatchlist().add('X', '離線加入')
    await nextTick()
    await vi.advanceTimersByTimeAsync(1_500)
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('error')
    expect(useWatchlist().items.value.some(i => i.code === 'X')).toBe(true) // 本地保留

    // 恢復連線；雲端此時有 Y
    sync.state.store = {
      updatedAt: 999,
      items: [item('Y', { addedAt: 700, updatedAt: 700 })],
    }
    sync.state.mode = 'ok'
    document.dispatchEvent(new Event('visibilitychange')) // 切回前景 → 立即同步
    await flushMicrotasks()

    const codes = useWatchlist().items.value.map(i => i.code)
    expect(codes).toContain('X') // 離線變更保留
    expect(codes).toContain('Y') // 遠端變更併入
    expect(syncApi.status.value).toBe('synced')
  })

  it('需求 8：同步寫入後無實際變更不重複推（不觸發自身 watchEffect 死循環）', async () => {
    await settleBaseline()

    // 手動再同步一輪（無任何本地變更）
    await syncApi.syncOnce()
    await flushMicrotasks()
    expect(sync.fn).toHaveBeenCalledTimes(4)

    // 等過 debounce 與額外時間：不應有自觸發的額外請求
    await vi.advanceTimersByTimeAsync(1_500)
    await vi.advanceTimersByTimeAsync(5_000)
    expect(sync.fn).toHaveBeenCalledTimes(4)

    // 對照組：本地真實變更 → 正好一輪新請求（GET + POST）
    useWatchlist().add('Z', '本機新增')
    await nextTick()
    await vi.advanceTimersByTimeAsync(1_500)
    await flushMicrotasks()
    expect(sync.fn).toHaveBeenCalledTimes(6)
    const lastPost = [...sync.calls].reverse().find(c => c.method === 'POST' && c.url !== 'https://www.npoint.io/documents')!
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

    const before = sync.fn.mock.calls.length
    wrapper.unmount() // cleanup：stopPolling + removeListeners + clear timers

    setVisibility('visible')
    await vi.advanceTimersByTimeAsync(120_000) // 若輪詢未停止會 +2
    document.dispatchEvent(new Event('visibilitychange')) // 若監聽器未移除會 +2
    window.dispatchEvent(new Event('focus'))

    expect(sync.fn.mock.calls.length).toBe(before)
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
    localStorage.setItem(SYNC_TOKEN_KEY, 'reload-token')
    localStorage.setItem(
      'stockpayday-watchlist',
      JSON.stringify([{ code: '2330', name: '台積電', type: 'stock', addedAt: 1000, updatedAt: 1000 }]),
    )

    const sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)

    const wl = await import('../useWatchlist')
    const syncMod = await import('../useWatchlistSync')

    await vi.waitFor(() => expect(sync.calls.length).toBe(2))

    const syncApi = syncMod.useWatchlistSync()
    expect(syncApi.bucketId.value).toBe('reload-token')
    expect(syncApi.syncActive.value).toBe(true)
    expect(wl.syncActiveRef.value).toBe(true) // 初始化同步 syncActiveRef
    expect(syncApi.status.value).toBe('synced')

    // GET 404 → POST 建立（含 localStorage 載入的本地清單）
    expect(sync.calls[0].url).toBe('https://api.npoint.io/reload-token')
    const post = sync.calls.find(c => c.method === 'POST' && c.url !== 'https://www.npoint.io/documents')!
    expect(post.body?.items.some(i => i.code === '2330')).toBe(true)

    syncMod.resetSyncState() // 清理 fresh module 的 timer/listener
  })

  it('F-26 localStorage 不可用（getItem 拋錯）→ 視同未配對、同步引擎不啟動', async () => {
    localStorage.setItem(SYNC_TOKEN_KEY, 'tok')
    const original = Storage.prototype.getItem
    Storage.prototype.getItem = () => {
      throw new Error('access denied')
    }
    try {
      const sync = createSyncMock()
      vi.stubGlobal('fetch', sync.fn)

      await import('../useWatchlist')
      const syncMod = await import('../useWatchlistSync')

      const syncApi = syncMod.useWatchlistSync()
      expect(syncApi.bucketId.value).toBe('')
      expect(syncApi.syncActive.value).toBe(false)
      expect(syncApi.status.value).toBe('disabled')
      await syncApi.syncOnce()
      expect(sync.calls).toHaveLength(0) // 視同未配對：不發任何 npoint.io 請求

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
