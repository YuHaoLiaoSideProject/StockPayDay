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
import type { WatchlistItem, WatchlistSyncDoc } from '../../types/watchlist'
import { useWatchlist, syncActiveRef } from '../useWatchlist'
import { useWatchlistSync, merge, resetSyncState } from '../useWatchlistSync'

/** 快速製造 WatchlistItem（測試用） */
function item(code: string, opts: Partial<WatchlistItem> = {}): WatchlistItem {
  return { code, addedAt: 100, ...opts }
}

/**
 * npoint.io fetch mock：可在測試中途切換行為（404/429/fail/401/500/POST 特定狀態）
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
  forcePostStatus?: number
  createdToken?: string
}

function createSyncMock() {
  const calls: SyncCall[] = []
  const state: SyncMockState = { mode: 'ok', store: null }
  const fn = vi.fn(async (input: unknown, init?: RequestInit) => {
    const url = String(input)
    const method = (init?.method as string) ?? 'GET'

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

    if (method === 'POST' && url === 'https://www.npoint.io/documents') {
      const token = state.createdToken ?? 'mock-token'
      calls.push({ url, method, status: 200 })
      return { ok: true, status: 200, json: async () => ({ token, api_url: `https://api.npoint.io/${token}` }) }
    }

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

function resetAll(): void {
  localStorage.clear()
  resetSyncState()
  useWatchlist().reset()
  vi.unstubAllGlobals()
}

async function flushMicrotasks(times = 40): Promise<void> {
  for (let i = 0; i < times; i++) await Promise.resolve()
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
    const local = [item('X', { addedAt: 200 })]
    const remote = [item('X', { addedAt: 100 })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].addedAt).toBe(200)
  })

  it('同股雙端變更以最後寫入者勝出（雲端較新）', () => {
    const local = [item('X', { addedAt: 100 })]
    const remote = [item('X', { addedAt: 200 })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].addedAt).toBe(200)
  })

  it('F-11b 墓碑為最終狀態：較新墓碑不被本地舊活躍資料覆蓋', () => {
    const local = [item('X', { addedAt: 50 })] // 舊的活躍項目
    const remote = [item('X', { addedAt: 100, deleted: true })] // 較新墓碑

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBe(true)
  })

  it('BDD Scenario 12 較新活躍項目勝過較早墓碑（重新追蹤）', () => {
    const local = [item('X', { addedAt: 200 })] // 較晚重新加入
    const remote = [item('X', { addedAt: 100, deleted: true })] // 較早墓碑

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBeUndefined()
    expect(result[0].addedAt).toBe(200)
  })

  it('同刻比對：墓碑（deleted）為最終狀態勝出', () => {
    const local = [item('X', { addedAt: 100 })]
    const remote = [item('X', { addedAt: 100, deleted: true })]

    const result = merge(local, remote)

    expect(result).toHaveLength(1)
    expect(result[0].deleted).toBe(true)
  })

  it('墓碑保留在陣列中（removed 的 code 仍存在於合併結果）', () => {
    const local = [item('2330', { addedAt: 100 })]
    const remote = [item('0056', { addedAt: 200, deleted: true })]

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

    const createCalls = sync.calls.filter(c => c.url === 'https://www.npoint.io/documents' && c.method === 'POST')
    expect(createCalls).toHaveLength(1)

    expect(result.token).toBe('new-sync-token-abc')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBe('new-sync-token-abc')

    expect(syncApi.bucketId.value).toBe('')
    expect(syncApi.syncActive.value).toBe(false)
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
    add('2330')

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
    expect(syncActiveRef.value).toBe(true)
    expect(syncApi.status.value).toBe('syncing')

    await flushMicrotasks()

    expect(syncApi.status.value).toBe('synced')
    expect(syncApi.lastSyncedAt.value).toBeTypeOf('number')
    expect(syncApi.lastError.value).toBeNull()
  })

  it('F-19 clearToken 清除 token、停用同步、syncActiveRef 回 false 且本地清單保留', async () => {
    const { add, items } = useWatchlist()
    add('2330')

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')

    expect(syncActiveRef.value).toBe(true)

    syncApi.clearToken()

    expect(syncApi.bucketId.value).toBe('')
    expect(localStorage.getItem(SYNC_TOKEN_KEY)).toBeNull()
    expect(syncApi.syncActive.value).toBe(false)
    expect(syncActiveRef.value).toBe(false)
    expect(syncApi.status.value).toBe('disabled')
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
      const { add, isWatched } = useWatchlist()
      add('2330')
      expect(isWatched('2330')).toBe(true)
    } finally {
      Storage.prototype.setItem = original
    }
  })

  it('syncActive 下 remove 走墓碑語意（syncActiveRef 生效）', () => {
    const { add, remove, items } = useWatchlist()
    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')

    add('2330')
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
    add('2330')
    add('0050')

    const syncApi = useWatchlistSync()
    syncApi.setToken('first-token')
    await flushMicrotasks()

    const get404 = sync.calls.filter(c => c.method === 'GET' && c.status === 404)
    expect(get404.length).toBeGreaterThanOrEqual(1)

    const postCalls = sync.calls.filter(c => c.method === 'POST' && c.url.startsWith('https://api.npoint.io/'))
    expect(postCalls).toHaveLength(1)
    expect(sync.state.store?.items.map(i => i.code).sort()).toEqual(['0050', '2330'])
  })

  it('F-09 非首次：GET 200 → merge 雲端與本地 → POST 回寫', async () => {
    sync.state.store = {
      updatedAt: Date.now(),
      items: [item('0050', { addedAt: 100 })],
    }

    const { add } = useWatchlist()
    add('2330')

    const syncApi = useWatchlistSync()
    syncApi.setToken('existing-token')
    await flushMicrotasks()

    const get200 = sync.calls.filter(c => c.method === 'GET' && c.status === 200)
    expect(get200.length).toBeGreaterThanOrEqual(1)

    const postCalls = sync.calls.filter(c => c.method === 'POST' && c.url.startsWith('https://api.npoint.io/'))
    expect(postCalls).toHaveLength(1)
    expect(sync.state.store?.items.map(i => i.code).sort()).toEqual(['0050', '2330'])
  })

  it('F-20 雲端與本地同步：本地較新 → 雲端被覆蓋', async () => {
    sync.state.store = {
      updatedAt: Date.now(),
      items: [item('2330', { addedAt: 100 })],
    }

    const { add } = useWatchlist()
    add('2330') // 本地較新（addedAt 為現在時間）

    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    expect(sync.state.store?.items).toHaveLength(1)
    expect(sync.state.store?.items[0].addedAt).toBeGreaterThan(100)
  })
})

// ============================================================
// 429 速率限制退避（F-16 / F-17）
// ============================================================
describe('429 速率限制退避', () => {
  let sync: SyncMock

  beforeEach(() => {
    resetAll()
    sync = createSyncMock()
    vi.stubGlobal('fetch', sync.fn)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    resetAll()
  })

  it('429 首次觸發退避：30s 後重試', async () => {
    sync.state.mode = '429'
    const syncApi = useWatchlistSync()
    syncApi.setToken('tok')
    await flushMicrotasks()

    expect(syncApi.status.value).toBe('error')
    expect(syncApi.lastError.value).toContain('速率限制')

    vi.advanceTimersByTime(30_000)
    await flushMicrotasks()

    expect(sync.calls.filter(c => c.method === 'GET').length).toBeGreaterThanOrEqual(2)
  })
})
