/**
 * WatchlistSyncSettings 元件單元測試（Phase 9 子任務 C — 設定 UI 與匯出/匯入備援）
 *
 * 對應測試計畫 F- 群組：
 * - F-01 啟動後記住同步碼並顯示「同步中…」
 * - F-06 未配對顯示設定區塊與說明
 * - F-07a/b/c 同步狀態顯示（同步中／已同步＋上次同步時間／失敗＋錯誤訊息）
 * - 429 退避訊息顯示（F-16/17 的 UI 呈現）
 * - F-19 停用同步（sync-token-clear）：token 清除、回到未配對、本地清單保留
 * - 立即同步：再次觸發 syncOnce（狀態回到「同步中…」）
 * - F-21 匯出內容為目前追蹤項目（不含已移除墓碑）
 * - F-22 匯入合併且不重複（本地已含 X，匯入 X+Y → X 一筆、Y 加入）
 * - F-23 匯入格式錯誤：顯示錯誤且本地清單不變
 *
 * 架構更新：使用 npoint.io 作為後端服務。
 * - 建立空間：POST https://www.npoint.io/documents → 回傳 { token }
 * - 同步讀寫：GET/POST https://api.npoint.io/{token}
 * - 無需 email 驗證，建立後立即可同步
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import WatchlistSyncSettings from '../WatchlistSyncSettings.vue'
import type { WatchlistItem, WatchlistSyncDoc } from '../../types/watchlist'
import { useWatchlist } from '../../composables/useWatchlist'
import { useWatchlistSync, resetSyncState } from '../../composables/useWatchlistSync'

type SyncMode = 'ok' | 'delay' | 'fail' | '429'

let syncMode: SyncMode = 'ok'
let syncStore: WatchlistSyncDoc | null = null
let createdToken = 'mock-token'

/** npoint.io fetch stub：非 npoint.io 請求不處理 */
const syncFetch = vi.fn(async (input: unknown, init?: RequestInit) => {
  const url = String(input)
  const method = (init?.method as string) ?? 'GET'
  if (!url.includes('npoint.io')) {
    return { ok: false, status: 404, text: async () => '', json: async () => null }
  }
  // fail/429 模式：所有請求都失敗
  if (syncMode === 'fail') throw new TypeError('連線錯誤')
  if (syncMode === '429') return { ok: false, status: 429, text: async () => 'rate limited', json: async () => null }
  // 建立空間：POST https://www.npoint.io/documents
  if (method === 'POST' && url === 'https://www.npoint.io/documents') {
    return { ok: true, status: 200, json: async () => ({ token: createdToken, api_url: `https://api.npoint.io/${createdToken}` }) }
  }
  if (syncMode === 'delay') return new Promise(() => {}) // 永不 resolve → 停留在「同步中…」

  // 同步讀取/寫入
  return { ok: true, status: 200, text: async () => '', json: async () => syncStore }
})

/** 只計同步請求（不含建立空間） */
function syncCallCount(): number {
  return syncFetch.mock.calls.filter(([u]) => {
    const url = String(u)
    return url.startsWith('https://api.npoint.io') // 只計算 api.npoint.io 的請求
  }).length
}

function findButtonByText(wrapper: VueWrapper, text: string) {
  const btn = wrapper.findAll('button').find(b => b.text().includes(text))
  if (!btn) throw new Error(`找不到按鈕：${text}`)
  return btn
}

beforeEach(() => {
  localStorage.clear()
  useWatchlist().reset()
  resetSyncState()
  syncMode = 'ok'
  syncStore = null
  createdToken = 'mock-token'
  syncFetch.mockClear()
  vi.stubGlobal('fetch', syncFetch)
  // Mock clipboard API (navigator.clipboard may not exist in happy-dom)
  if (!navigator.clipboard) {
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: vi.fn().mockResolvedValue(undefined) },
      configurable: true,
    })
  } else {
    navigator.clipboard.writeText = vi.fn().mockResolvedValue(undefined)
  }
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('WatchlistSyncSettings（設定 UI）', () => {
  it('F-06 未配對時顯示同步設定區塊、說明、建立按鈕與同步碼備援', () => {
    const wrapper = mount(WatchlistSyncSettings)

    expect(wrapper.find('[data-testid="watchlist-sync-settings"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('🔄 跨裝置同步（選配）')
    expect(wrapper.text()).toContain('不設定則完全不影響現有功能')
    // 建立同步空間按鈕為主要方式
    expect(wrapper.find('[data-testid="sync-create-btn"]').exists()).toBe(true)
    // 同步碼備援（預設隱藏）
    expect(wrapper.find('[data-testid="sync-token-input"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="sync-token-toggle"]').exists()).toBe(true)
  })

  it('建立同步空間：建立空間 → 顯示 token + 同步已自動啟動', async () => {
    syncMode = 'delay' // 延遲 → 停留在同步中
    createdToken = 'new-sync-token-123'
    const wrapper = mount(WatchlistSyncSettings)

    await wrapper.find('[data-testid="sync-create-btn"]').trigger('click')
    await flushPromises()
    await nextTick() // 等待 Vue 重新渲染

    // 建立空間請求
    const createCalls = syncFetch.mock.calls.filter(([u, opts]) =>
      String(u) === 'https://www.npoint.io/documents' && (opts as any)?.method === 'POST'
    )
    expect(createCalls).toHaveLength(1)

    // 顯示 token
    expect(wrapper.find('[data-testid="token-display"]').text()).toBe('new-sync-token-123')
    expect(wrapper.text()).toContain('同步空間已建立')
    expect(wrapper.text()).toContain('請將此同步碼貼到其他裝置')

    // 顯示「複製」按鈕
    expect(wrapper.find('[data-testid="copy-token"]').exists()).toBe(true)

    // 顯示「開始同步」按鈕
    expect(wrapper.find('[data-testid="start-sync"]').exists()).toBe(true)

    // token 存入 localStorage
    expect(localStorage.getItem('stockpayday-sync-token')).toBe('new-sync-token-123')
  })

  it('建立同步空間失敗：留在建立畫面、顯示錯誤訊息', async () => {
    syncMode = 'fail'
    const wrapper = mount(WatchlistSyncSettings)

    await wrapper.find('[data-testid="sync-create-btn"]').trigger('click')
    await flushPromises()

    // 錯誤訊息
    expect(wrapper.find('[data-testid="sync-create-error"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('連線錯誤')

    // 仍在建立畫面
    expect(wrapper.find('[data-testid="sync-create-btn"]').exists()).toBe(true)
    expect(localStorage.getItem('stockpayday-sync-token')).toBeNull()
  })

  it('複製 token：呼叫 navigator.clipboard.writeText', async () => {
    createdToken = 'copy-test-token'
    const wrapper = mount(WatchlistSyncSettings)

    await wrapper.find('[data-testid="sync-create-btn"]').trigger('click')
    await flushPromises()
    await nextTick() // 等待 Vue 重新渲染

    await wrapper.find('[data-testid="copy-token"]').trigger('click')
    await nextTick()

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('copy-test-token')
    expect(wrapper.text()).toContain('已複製')
  })

  it('開始同步：點擊後切換到同步狀態區塊', async () => {
    syncMode = 'delay'
    createdToken = 'verify-token'
    const wrapper = mount(WatchlistSyncSettings)

    await wrapper.find('[data-testid="sync-create-btn"]').trigger('click')
    await flushPromises()
    await nextTick() // 等待 Vue 重新渲染

    // 點擊「開始同步」
    await wrapper.find('[data-testid="start-sync"]').trigger('click')
    await nextTick()

    // 切換到同步狀態區塊
    expect(wrapper.text()).toContain('同步中…')
    expect(wrapper.find('[data-testid="token-display"]').exists()).toBe(false)
  })

  it('F-01 同步碼直接輸入啟動：trim 後寫入 localStorage、切換已配對並顯示「同步中…」', async () => {
    syncMode = 'delay' // fetch 延遲 → 狀態停留「同步中…」
    const wrapper = mount(WatchlistSyncSettings)

    // 展開同步碼輸入
    await wrapper.find('[data-testid="sync-token-toggle"]').trigger('click')
    await nextTick()

    await wrapper.find('[data-testid="sync-token-input"]').setValue('  test-token  ')
    // Click the submit button AND trigger form submit (happy-dom may not propagate)
    const submitBtn = wrapper.find('[data-testid="sync-token-submit"]')
    await submitBtn.trigger('click')
    // Also trigger form submit directly as fallback
    const forms = wrapper.findAll('form')
    const tokenForm = forms.find(f => f.find('[data-testid="sync-token-input"]').exists())
    if (tokenForm) await tokenForm.trigger('submit')
    await nextTick()

    expect(localStorage.getItem('stockpayday-sync-token')).toBe('test-token')
    expect(wrapper.find('[data-testid="sync-create-btn"]').exists()).toBe(false) // 已配對分支
    expect(wrapper.text()).toContain('同步中…')
    expect(wrapper.text()).not.toContain('上次同步')
    // 啟動後立即發起一次同步（pull）
    expect(syncCallCount()).toBe(1)
  })

  it('F-07b 已配對同步完成：顯示「已同步」並附上次同步時間', async () => {
    syncMode = 'ok'
    syncStore = { updatedAt: Date.now(), items: [] }
    const wrapper = mount(WatchlistSyncSettings)

    useWatchlistSync().setToken('test-token')
    await flushPromises()

    expect(wrapper.text()).toContain('已同步')
    expect(wrapper.text()).toContain('上次同步')
    expect(wrapper.text()).not.toContain('同步中…')
  })

  it('F-07c 同步失敗：顯示「同步失敗」與錯誤訊息', async () => {
    syncMode = 'fail'
    const wrapper = mount(WatchlistSyncSettings)

    useWatchlistSync().setToken('bad-token')
    await flushPromises()

    expect(wrapper.text()).toContain('同步失敗')
    expect(wrapper.text()).toContain('連線錯誤')
    expect(wrapper.find('[data-testid="watchlist-sync-error"]').exists()).toBe(true)
  })

  it('429 速率限制：顯示退避訊息（速率限制（429），30 秒後重試）', async () => {
    syncMode = '429'
    const wrapper = mount(WatchlistSyncSettings)

    useWatchlistSync().setToken('test-token')
    await flushPromises()

    expect(wrapper.text()).toContain('同步失敗')
    expect(wrapper.text()).toContain('速率限制（429）')
    expect(wrapper.text()).toContain('30 秒後重試')
  })

  it('立即同步：再次觸發 syncOnce（狀態回到「同步中…」）', async () => {
    syncMode = 'ok'
    syncStore = { updatedAt: Date.now(), items: [] }
    const wrapper = mount(WatchlistSyncSettings)
    useWatchlistSync().setToken('test-token')
    await flushPromises()
    expect(wrapper.text()).toContain('已同步')

    syncMode = 'delay'
    const before = syncCallCount()
    await findButtonByText(wrapper, '立即同步').trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('同步中…')
    expect(syncCallCount()).toBe(before + 1)
  })

  it('F-19 停用同步：token 清除、回到未配對區塊、本地追蹤清單保留', async () => {
    const { add, isWatched } = useWatchlist()
    add('2330', '台積電')

    syncMode = 'delay'
    const wrapper = mount(WatchlistSyncSettings)
    useWatchlistSync().setToken('test-token')
    await nextTick()
    expect(wrapper.text()).toContain('同步中…') // 已配對

    await wrapper.find('[data-testid="sync-token-clear"]').trigger('click')
    await nextTick()

    expect(localStorage.getItem('stockpayday-sync-token')).toBeNull()
    expect(wrapper.find('[data-testid="sync-create-btn"]').exists()).toBe(true) // 回到未配對分支
    expect(isWatched('2330')).toBe(true) // 停用不刪本地清單
  })
})

describe('WatchlistSyncSettings（匯出/匯入備援）', () => {
  async function openBackup(): Promise<VueWrapper> {
    const wrapper = mount(WatchlistSyncSettings)
    await wrapper.find('[data-testid="sync-backup-toggle"]').trigger('click')
    expect(wrapper.find('[data-testid="sync-backup-body"]').exists()).toBe(true)
    return wrapper
  }

  it('F-21 匯出內容為目前追蹤項目（含 ETF／特別股）；不含已移除墓碑', async () => {
    const { items } = useWatchlist()
    items.value = [
      { code: '2330', name: '台積電', type: 'stock', addedAt: 1, updatedAt: 1 },
      { code: '0056', name: '元大高股息', type: 'etf', addedAt: 2, updatedAt: 2 },
      { code: '2884', name: '玉山金', type: 'preferred', addedAt: 3, updatedAt: 3, deleted: true },
    ]

    const wrapper = await openBackup()
    await wrapper.find('[data-testid="sync-export-button"]').trigger('click')
    await nextTick()

    const textarea = wrapper.find('[data-testid="sync-export-text"]')
    expect(textarea.exists()).toBe(true)
    const content = (textarea.element as HTMLTextAreaElement).value
    const parsed = JSON.parse(content) as WatchlistItem[]
    expect(parsed.map(i => i.code)).toEqual(['2330', '0056'])
    expect(parsed.some(i => i.deleted)).toBe(false)
    expect(content).not.toContain('2884')
  })

  it('F-22 匯入合併且不重複：本地已含 X，匯入 X+Y 後 X 維持一筆、Y 加入', async () => {
    const { add, items } = useWatchlist()
    add('2330', '台積電', 'stock')

    const wrapper = await openBackup()
    const importText = JSON.stringify([
      { code: '2330', name: '台積電', type: 'stock', addedAt: 100, updatedAt: 100 },
      { code: '0056', name: '元大高股息', type: 'etf', addedAt: 101, updatedAt: 101 },
    ])
    await wrapper.find('[data-testid="sync-import-text"]').setValue(importText)
    await wrapper.find('[data-testid="sync-import-submit"]').trigger('click')
    await nextTick()

    const codes = items.value.map(i => i.code)
    expect(codes).toEqual(['2330', '0056'])
    expect(items.value.filter(i => i.code === '2330')).toHaveLength(1) // 不重複加入
    expect(wrapper.find('[data-testid="sync-import-message"]').text()).toBe('已合併 1 支證券')
  })

  it('F-23 匯入格式錯誤：顯示錯誤提示且本地清單不變', async () => {
    const { add, items } = useWatchlist()
    add('2330', '台積電')

    const wrapper = await openBackup()
    await wrapper.find('[data-testid="sync-import-text"]').setValue('this is not json')
    await wrapper.find('[data-testid="sync-import-submit"]').trigger('click')
    await nextTick()

    const err = wrapper.find('[data-testid="sync-import-error"]')
    expect(err.exists()).toBe(true)
    expect(err.text()).toContain('匯入格式錯誤')
    expect(items.value.map(i => i.code)).toEqual(['2330']) // 本地不變
  })

  it('F-23b 匯入內容欄位錯誤（缺少有效 code）：顯示錯誤且本地清單不變', async () => {
    const { add, items } = useWatchlist()
    add('2330', '台積電')

    const wrapper = await openBackup()
    await wrapper.find('[data-testid="sync-import-text"]').setValue('[{"name":"無代號"}]')
    await wrapper.find('[data-testid="sync-import-submit"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-testid="sync-import-error"]').text()).toContain('匯入格式錯誤')
    expect(items.value.map(i => i.code)).toEqual(['2330'])
  })
})
