/**
 * kvdb.io mock helper（Phase 9 E2E 基礎設施，對應測試計畫 §3.7 mock 策略）
 *
 * - 以 page.route('https://kvdb.io/**') 攔截真實 kvdb.io 請求（E2E 一律不連真實服務）
 * - 以 page.route('**/kvdb-proxy*') 攔截 Cloudflare Worker 請求
 * - 記憶體 Map 模擬雲端文件：同一 mock 物件傳給兩個 page → 模擬兩台裝置共用雲端
 * - 可於測試中途切換 `mode`：ok（GET 404/200、POST 200）、429、fail（網路失敗）
 * - `requests` 計數供「零請求／停止請求」斷言（E2E-02/05/19）
 *
 * kvdb 契約（與 useWatchlistSync 的 pull/push 對應）：
 *   GET  https://kvdb.io/stockpayday/user:me:watchlist?access_token=… → 200 doc | 404（首次）
 *   POST https://kvdb.io/… → 200（寫入 doc）
 *
 * Worker 契約（與 useWatchlistSync 的 createAccount 對應）：
 *   POST /kvdb-proxy { email } → 200 { access_token, bucket_id }
 */
import type { Page } from '@playwright/test'
import type { WatchlistSyncDoc } from '../../src/types/watchlist'

export type KvdbMode = 'ok' | '429' | 'fail'

/** 單一 token 可覆寫的行為（預留：無效配對碼 401 情境） */
export type KvdbTokenMode = 'ok' | '404' | '429' | 'fail' | '401'

export interface KvdbMock {
  /** 記憶體雲端文件：URL path（如 `stockpayday/user:me:watchlist`）→ 文件 */
  store: Map<string, WatchlistSyncDoc>
  /** 全域行為模式（可於測試中途切換，如 fail→ok 模擬恢復連線） */
  mode: KvdbMode
  /** 依 access_token 個別覆寫模式（優先於 mode） */
  modeByToken: Map<string, KvdbTokenMode>
  /** kvdb 請求計數 */
  requests: number
  /** Worker 請求計數 */
  workerRequests: number
}

export const CLOUD_KEY = 'stockpayday/user:me:watchlist'

export function createKvdbMock(mode: KvdbMode = 'ok'): KvdbMock {
  return { store: new Map(), mode, modeByToken: new Map(), requests: 0, workerRequests: 0 }
}

function resolveMode(mock: KvdbMock, token: string): KvdbMode | KvdbTokenMode {
  return mock.modeByToken.get(token) ?? mock.mode
}

export async function installKvdbMock(page: Page, mock: KvdbMock): Promise<void> {
  await page.route('https://kvdb.io/**', async route => {
    mock.requests++
    const req = route.request()
    const url = new URL(req.url())
    const key = url.pathname.replace(/^\//, '')
    const token = url.searchParams.get('access_token') ?? ''
    const mode = resolveMode(mock, token)

    if (mode === 'fail') return route.abort('failed') // 網路失敗
    if (mode === '429') return route.fulfill({ status: 429, contentType: 'text/plain', body: 'rate limited' })
    if (mode === '401') return route.fulfill({ status: 401, contentType: 'text/plain', body: 'unauthorized' })
    if (mode === '404') return route.fulfill({ status: 404, body: '' })

    if (req.method() === 'GET') {
      if (!mock.store.has(key)) return route.fulfill({ status: 404, body: '' }) // 首次：雲端尚無文件
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mock.store.get(key)),
      })
    }
    if (req.method() === 'POST') {
      mock.store.set(key, req.postDataJSON() as WatchlistSyncDoc)
      return route.fulfill({ status: 200, body: '' })
    }
    return route.fulfill({ status: 405, body: '' })
  })

  // Mock Cloudflare Worker（kvdb-proxy）
  await page.route('**/kvdb-proxy*', async route => {
    mock.workerRequests++
    const req = route.request()
    if (req.method() === 'OPTIONS') {
      return route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*' } })
    }
    if (req.method() === 'POST') {
      const body = req.postDataJSON() as { email?: string }
      if (!body?.email) {
        return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ error: 'Email required' }) })
      }
      // 回傳模擬 token（使用 email 當作 seed 產生唯一 token）
      const fakeToken = `worker-token-${btoa(body.email).replace(/=/g, '')}`
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access_token: fakeToken, bucket_id: 'mock-bucket' }),
      })
    }
    return route.fulfill({ status: 405, body: '' })
  })
}

/** 輪詢等待（測試端真實時間，不受 page.clock 影響） */
export async function waitUntil(
  fn: () => boolean,
  timeoutMs = 8000,
  stepMs = 50
): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (!fn()) {
    if (Date.now() > deadline) throw new Error(`waitUntil timeout（${timeoutMs}ms）`)
    await new Promise(r => setTimeout(r, stepMs))
  }
}

/**
 * 模擬「使用者把裝置/分頁切回前景」：
 * bringToFront（真實 tab 啟動）＋ 手動 dispatch focus / visibilitychange
 * （headless 環境 bringToFront 不保證觸發原生事件，故手動補發；
 * 與 useWatchlistSync 的 window focus / document visibilitychange 監聽對應）
 */
export async function activatePage(page: Page): Promise<void> {
  await page.bringToFront()
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { value: 'visible', configurable: true })
    window.dispatchEvent(new Event('focus'))
    document.dispatchEvent(new Event('visibilitychange'))
  })
}

export function cloudDoc(mock: KvdbMock): WatchlistSyncDoc | null {
  return mock.store.get(CLOUD_KEY) ?? null
}

export function cloudCodes(mock: KvdbMock): string[] {
  return cloudDoc(mock)?.items.map(i => i.code) ?? []
}