/**
 * kvdb.io mock helper（Phase 9 E2E 基礎設施，對應測試計畫 §3.7 mock 策略）
 *
 * - 以 page.route('https://kvdb.io/**') 攔截真實 kvdb.io 請求（E2E 一律不連真實服務）
 * - 記憶體 Map 模擬雲端文件：同一 mock 物件傳給兩個 page → 模擬兩台裝置共用雲端
 * - 可於測試中途切換 `mode`：ok（GET 404/200、POST 200）、429、fail（網路失敗）
 * - `requests` 計數供「零請求／停止請求」斷言（E2E-02/05/19）
 *
 * kvdb 契約（與 useWatchlistSync 的 pull/push 對應）：
 *   GET  https://kvdb.io/{bucket_id}/user:me:watchlist → 200 doc | 404（首次）
 *   POST https://kvdb.io/{bucket_id}/... → 200（寫入 doc）
 *
 * 建 bucket 契約（與 useWatchlistSync 的 createAccount 對應）：
 *   POST https://kvdb.io/ with body email=xxx → 200 純文字 bucket_id
 */
import type { Page } from '@playwright/test'
import type { WatchlistSyncDoc } from '../../src/types/watchlist'

export type KvdbMode = 'ok' | '429' | 'fail'

/** 單一 token 可覆寫的行為（預留：無效配對碼 401 情境） */
export type KvdbTokenMode = 'ok' | '404' | '429' | 'fail' | '401'

export interface KvdbMock {
  /** 記憶體雲端文件：URL path（如 `{bucket_id}/user:me:watchlist`）→ 文件 */
  store: Map<string, WatchlistSyncDoc>
  /** 全域行為模式（可於測試中途切換，如 fail→ok 模擬恢復連線） */
  mode: KvdbMode
  /** 依 access_token 個別覆寫模式（優先於 mode） */
  modeByToken: Map<string, KvdbTokenMode>
  /** kvdb 請求計數（含建 bucket + 同步讀寫） */
  requests: number
  /** 建 bucket 回傳的 bucket_id（預設 'mock-bucket'） */
  createdBucketId: string
}

export const CLOUD_KEY_SUFFIX = 'user:me:watchlist'

export function createKvdbMock(mode: KvdbMode = 'ok'): KvdbMock {
  return { store: new Map(), mode, modeByToken: new Map(), requests: 0, createdBucketId: 'mock-bucket' }
}

function resolveMode(mock: KvdbMock, token: string): KvdbMode | KvdbTokenMode {
  return mock.modeByToken.get(token) ?? mock.mode
}

export async function installKvdbMock(page: Page, mock: KvdbMock): Promise<void> {
  await page.route('https://kvdb.io/**', async route => {
    mock.requests++
    const req = route.request()
    const url = new URL(req.url())
    const pathname = url.pathname.replace(/^\//, '')
    const token = url.searchParams.get('access_token') ?? ''
    const mode = resolveMode(mock, token)

    if (mode === 'fail') return route.abort('failed') // 網路失敗
    if (mode === '429') return route.fulfill({ status: 429, contentType: 'text/plain', body: 'rate limited' })
    if (mode === '401') return route.fulfill({ status: 401, contentType: 'text/plain', body: 'unauthorized' })
    if (mode === '404') return route.fulfill({ status: 404, body: '' })

    // 建 bucket：POST https://kvdb.io/（pathname 為空）
    // 注意：happy-dom 的 fetch 可能不會正規化 URL（不加 trailing slash）
    if (req.method() === 'POST' && (pathname === '' || pathname === '/')) {
      return route.fulfill({
        status: 200,
        contentType: 'text/plain',
        body: mock.createdBucketId,
      })
    }

    // 同步讀取：GET https://kvdb.io/{bucket_id}/{key}
    if (req.method() === 'GET') {
      if (!mock.store.has(pathname)) return route.fulfill({ status: 404, body: '' }) // 首次：雲端尚無文件
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mock.store.get(pathname)),
      })
    }

    // 同步寫入：POST https://kvdb.io/{bucket_id}/{key}
    if (req.method() === 'POST') {
      mock.store.set(pathname, req.postDataJSON() as WatchlistSyncDoc)
      return route.fulfill({ status: 200, body: '' })
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

export function cloudDoc(mock: KvdbMock, bucketId = 'mock-bucket'): WatchlistSyncDoc | null {
  return mock.store.get(`${bucketId}/${CLOUD_KEY_SUFFIX}`) ?? null
}

export function cloudCodes(mock: KvdbMock, bucketId = 'mock-bucket'): string[] {
  return cloudDoc(mock, bucketId)?.items.map(i => i.code) ?? []
}
