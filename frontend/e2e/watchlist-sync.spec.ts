/**
 * E2E：Phase 9 跨裝置追蹤清單同步（子任務 D）
 *
 * 對應 BDD：docs/bdds/phases/phase-9-跨裝置追蹤清單同步.feature
 * 對應測試計畫 §3：案例 E2E-01…E2E-23（kvdb 一律以 page.route mock，不連真實服務）
 *
 * 覆蓋重點（任務需求）：
 * - 未配對操作追蹤 → 零同步請求（計數 kvdb 請求 = 0）
 * - 貼配對碼啟用 → 兩 tab/page 跨裝置同步：A 增刪寫回雲端、B 切回即收到；移除以墓碑傳播至 B 消失
 * - 首次配對（雲端無文件）→ 上傳建立、狀態「已同步」＋時間、reload 後仍已配對
 * - 離線操作正常（本地增刪保留、顯示同步失敗）→ 恢復後自動合併回「已同步」
 * - 429 → UI 顯示退避訊息（30 秒後重試）、退避期間本機操作正常、之後自動恢復「已同步」
 * - 停用同步 → 本地清單保留、不再發同步請求
 * - 匯出內容不含已移除項目；匯入合併不重複；匯入格式錯誤顯示錯誤且本地不變
 */
import { test, expect, type Page } from '@playwright/test'
import {
  createKvdbMock,
  installKvdbMock,
  waitUntil,
  activatePage,
  cloudDoc,
  cloudCodes,
  CLOUD_KEY,
  type KvdbMock,
} from './helpers/kvdbMock'

const TOKEN_KEY = 'stockpayday-sync-token'
const WATCHLIST_URL = '/#/watchlist'

// ── UI helpers ────────────────────────────────────────────────────────────────

const wlSearch = (page: Page) => page.locator('[data-testid="watchlist-search"] .search-input')
const wlHeart = (page: Page, code: string) =>
  page.locator(`[data-testid="watchlist-search"] .search-results [data-testid="heart-${code}"]`)

async function gotoWatchlist(page: Page): Promise<void> {
  await page.goto(WATCHLIST_URL)
  await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })
}

async function searchStock(page: Page, code: string) {
  const input = wlSearch(page)
  // 下拉關閉的唯一機制是 SearchBar @blur 的 150ms 計時；並行環境主執行緒繁忙時該
  // 計時可能延後觸發，在下次 fill 開啟下拉後才關閉它 → 重試＋等待殘留計時先觸發完畢。
  // fill 為整值覆蓋（不殘留舊 query），click 聚焦（@focus 亦會重開下拉）。
  for (let attempt = 0; attempt < 3; attempt++) {
    await input.click()
    await input.fill(code)
    if (await wlHeart(page, code).isVisible().catch(() => false)) break
    await page.waitForTimeout(300) // 讓殘留的 @blur 計時先觸發完畢
  }
  await expect(wlHeart(page, code)).toBeVisible()
  return wlHeart(page, code)
}

async function addStock(page: Page, code: string): Promise<void> {
  await (await searchStock(page, code)).click()
}

async function removeStock(page: Page, code: string): Promise<void> {
  await (await searchStock(page, code)).click()
}

async function pair(page: Page, token: string): Promise<void> {
  // Use token input fallback for direct pairing
  await page.locator('[data-testid="sync-token-toggle"]').click()
  await page.locator('[data-testid="sync-token-input"]').fill(token)
  await page.locator('[data-testid="sync-token-submit"]').click()
}

async function pairByEmail(page: Page, email: string): Promise<void> {
  await page.locator('[data-testid="sync-email-input"]').fill(email)
  await page.locator('[data-testid="sync-email-submit"]').click()
}

async function expectSynced(page: Page): Promise<void> {
  await expect(page.locator('.sync-status-info')).toContainText('已同步')
}

async function expectCount(page: Page, n: number): Promise<void> {
  await expect(page.locator('.watchlist-count')).toContainText(`已追蹤 ${n} 支證券`)
}

/** header 徽章（注意：已配對時含墓碑數，僅用於新增方向斷言） */
async function expectBadge(page: Page, n: number): Promise<void> {
  await expect(page.locator('.watchlist-badge')).toHaveText(String(n))
}

function row(page: Page, code: string) {
  return page.locator('.watchlist-item-row', { hasText: code })
}

// ── 測試 ─────────────────────────────────────────────────────────────────────

test.describe('Phase 9 跨裝置追蹤清單同步（E2E）', () => {
  test('E2E-02/05/06 未配對：顯示設定區塊、email 輸入框、空白無法啟動、既有操作零同步請求', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    // 未配對顯示同步設定區塊（E2E-06）
    await expect(page.locator('[data-testid="watchlist-sync-settings"]')).toBeVisible()
    await expect(page.locator('.sync-pairing .sync-title')).toContainText('🔄 跨裝置同步（選配）')
    await expect(page.locator('.sync-pairing .sync-desc')).toContainText('不設定則完全不影響現有功能')

    // 顯示 email 輸入框（主要方式）
    await expect(page.locator('[data-testid="sync-email-input"]')).toBeVisible()
    await expect(page.locator('[data-testid="sync-email-submit"]')).toBeVisible()

    // 空白 email 無法啟動（E2E-02）：仍為未配對、無任何 kvdb 請求
    await page.locator('[data-testid="sync-email-submit"]').click()
    await expect(page.locator('[data-testid="sync-email-input"]')).toBeVisible()
    expect(await page.evaluate(k => localStorage.getItem(k), TOKEN_KEY)).toBeNull()

    // 既有操作與現況完全一致（E2E-05）：搜尋、加入、切換顯示模式、移除
    await addStock(page, '2330')
    await expectBadge(page, 1)
    await expectCount(page, 1)
    await page.locator('button[data-view="list"]').click()
    await expect(page.locator('.watchlist-all-items')).toBeVisible()
    await page.locator('button[data-view="calendar"]').click()
    await expect(page.locator('.calendar')).toBeVisible()
    await removeStock(page, '2330')
    await expect(page.locator('.watchlist-badge')).toBeHidden()
    await expect(page.locator('.watchlist-empty')).toBeVisible()

    // 零同步請求
    expect(mock.requests).toBe(0)
  })

  test('E2E-03/01 首次配對（雲端無文件）：上傳建立雲端清單、已同步＋時間、本地不變、reload 後仍配對', async ({ page }) => {
    const mock = createKvdbMock('ok') // store 空 → GET 404（首次）
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    // 先加入 2330（未配對）
    await addStock(page, '2330')
    await expectBadge(page, 1)

    // 貼配對碼啟用 → GET 404 → POST 建立雲端文件
    await pair(page, 'token-phase9')
    await expectSynced(page)
    await expect(page.locator('.sync-status-info')).toContainText(/上次同步 \d{1,2}:\d{2}:\d{2}/)
    await expect(page.locator('[data-testid="watchlist-sync-error"]')).toBeHidden()

    // 雲端收到 POST 且 body 含 2330；本機不變（仍恰一筆）
    await waitUntil(() => cloudCodes(mock).includes('2330'))
    expect(cloudCodes(mock)).toEqual(['2330'])
    const doc = cloudDoc(mock)!
    expect(doc.items.length).toBe(1)
    await expectBadge(page, 1)

    // 配對碼記住於本機 → reload 後仍已配對並自動同步
    expect(await page.evaluate(k => localStorage.getItem(k), TOKEN_KEY)).toBe('token-phase9')
    await page.reload()
    await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('[data-testid="sync-email-input"]')).toBeHidden() // 已配對分支
    await expectSynced(page)
    await expectBadge(page, 1)
  })

  test('E2E-04 首次配對（雲端已有清單）：本機 2330 與雲端 0056 合併為並集', async ({ page }) => {
    const mock = createKvdbMock('ok')
    mock.store.set(CLOUD_KEY, {
      updatedAt: 1,
      items: [{ code: '0056', name: '元大高股息', type: 'etf', addedAt: 1, updatedAt: 1 }],
    })
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')
    await expectBadge(page, 1)

    await pair(page, 'token-phase9')
    await expectSynced(page)

    // 合併呈現為並集：兩支都在、狀態已同步
    await expectCount(page, 2)
    await expect(page.locator('body')).toContainText('0056')
    await expect(row(page, '2330')).toHaveCount(1)
    await waitUntil(() => cloudCodes(mock).includes('0056'))
    expect(cloudCodes(mock)).toEqual(expect.arrayContaining(['2330', '0056']))
  })

  test('E2E-09/11 跨裝置：tab A 增刪寫回雲端，tab B 切回即收到（新增與移除墓碑傳播）', async ({ browser }) => {
    const context = await browser.newContext()
    const pageA = await context.newPage()
    const pageB = await context.newPage()

    const mock = createKvdbMock('ok')
    await installKvdbMock(pageA, mock)
    await installKvdbMock(pageB, mock)

    try {
      // tab A：配對 + 新增 2330 → 寫回雲端
      await pageA.goto(WATCHLIST_URL)
      await expect(pageA.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })
      await addStock(pageA, '2330')
      await pair(pageA, 'token-cross-device')
      await expectSynced(pageA)
      await waitUntil(() => cloudCodes(mock).includes('2330'))

      // tab B（同 context，localStorage 共享配對碼）：載入即自動同步 → 收到 2330
      await activatePage(pageB)
      await pageB.goto(WATCHLIST_URL)
      await expect(pageB.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })
      await expectBadge(pageB, 1)
      await expect(row(pageB, '2330')).toHaveCount(1)

      // tab A 新增 2317 → 1.5s debounce 自動寫回雲端
      await activatePage(pageA)
      await addStock(pageA, '2317')
      await expectBadge(pageA, 2)
      await waitUntil(() => cloudCodes(mock).includes('2317'))

      // tab B 切回（focus/可見）→ 自動拉取合併 → 收到 2317
      await activatePage(pageB)
      await expectBadge(pageB, 2)
      await expect(row(pageB, '2317')).toHaveCount(1)

      // tab A 移除 2317（已配對 → 墓碑語意）→ 墓碑寫回雲端
      await activatePage(pageA)
      await removeStock(pageA, '2317')
      await expectCount(pageA, 1) // 本機立即排除（activeItems 不含墓碑）
      await expect(row(pageA, '2317')).toHaveCount(0)
      await waitUntil(() => {
        const item = cloudDoc(mock)?.items.find(i => i.code === '2317')
        return item?.deleted === true
      })

      // tab B 切回 → 墓碑傳播 → 2317 從 B 消失
      await activatePage(pageB)
      await expectCount(pageB, 1)
      await expect(row(pageB, '2317')).toHaveCount(0)
      await wlSearch(pageB).fill('2317')
      await expect(wlHeart(pageB, '2317')).toBeVisible()
      await expect(wlHeart(pageB, '2317')).not.toHaveClass(/watched/)
      await expect(wlHeart(pageB, '2317')).toHaveAttribute('aria-pressed', 'false')
      // 兩裝置內容一致（皆剩 2330）
      await expect(row(pageB, '2330')).toHaveCount(1)
      await expect(row(pageA, '2330')).toHaveCount(1)
    } finally {
      await context.close()
    }
  })

  test('E2E-14/15 離線：增刪正常、顯示同步失敗、本地保留；恢復連線後自動合併回「已同步」', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    // 已配對且已同步
    await addStock(page, '2330')
    await pair(page, 'token-offline')
    await expectSynced(page)

    // 進入離線（網路失敗）→ 本機增刪正常、同步失敗
    mock.mode = 'fail'
    await addStock(page, '2317')
    await expectBadge(page, 2)
    await expectCount(page, 2)
    await page.locator('.sync-actions .btn-secondary').click() // 立即同步 → 失敗
    await expect(page.locator('.sync-status-info')).toContainText('同步失敗')
    await expect(page.locator('[data-testid="watchlist-sync-error"]')).toBeVisible()

    // reload（仍離線）：本地清單自 localStorage 完整保留
    await page.reload()
    await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })
    await expectBadge(page, 2)
    await expectCount(page, 2)

    // 恢復連線 → 自動合併離線期間變更 → 已同步（不需重貼配對碼）
    await expect(page.locator('[data-testid="watchlist-sync-error"]')).toBeVisible() // 等 init 同步失敗結束
    mock.mode = 'ok'
    await page.waitForTimeout(300)
    await activatePage(page)
    await page.locator('.sync-actions .btn-secondary').click()
    await expectSynced(page)
    await expectCount(page, 2)
    await waitUntil(() => cloudCodes(mock).includes('2317'))
    expect(cloudCodes(mock)).toEqual(expect.arrayContaining(['2330', '2317']))
  })

  test('E2E-16 429 速率限制：顯示退避訊息（30 秒後重試）、退避期間本機操作正常、自動恢復「已同步」', async ({ page }) => {
    await page.clock.install({ time: new Date('2024-01-01T12:00:00') })
    const mock = createKvdbMock('429')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)
    await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 10000 })

    // 貼配對碼 → 同步嘗試 → 429 → 退避排程（30s）
    await pair(page, 'token-429')
    await expect(page.locator('.sync-status-info')).toContainText('同步失敗')
    const err = page.locator('[data-testid="watchlist-sync-error"]')
    await expect(err).toContainText('速率限制（429）')
    await expect(err).toContainText('30 秒後重試')

    // 退避期間本機追蹤操作完全正常（狀態仍維持退避訊息）
    await addStock(page, '2330')
    await expectBadge(page, 1)
    await expectCount(page, 1)
    await expect(err).toContainText('30 秒後重試')

    // 雲端恢復 → 退避結束自動重試單次 → 已同步
    mock.mode = 'ok'
    await page.clock.fastForward(31_000)
    await expectSynced(page)
    await waitUntil(() => cloudCodes(mock).includes('2330'))
    await expectBadge(page, 1)
  })

  test('E2E-19 停用同步：本地清單保留、不再發同步請求', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')
    await pair(page, 'token-disable')
    await expectSynced(page)
    const requestsAfterPair = mock.requests
    expect(requestsAfterPair).toBeGreaterThan(0)

    // 停用
    await page.locator('[data-testid="sync-token-clear"]').click()
    await expect(page.locator('[data-testid="sync-email-input"]')).toBeVisible() // 回到未配對
    await expect(page.locator('.sync-status-info')).toBeHidden()
    expect(await page.evaluate(k => localStorage.getItem(k), TOKEN_KEY)).toBeNull()
    await expect(page.locator('[data-testid="watchlist-sync-error"]')).toBeHidden()

    // 本地清單完整保留
    await expectBadge(page, 1)
    await expectCount(page, 1)
    await expect(row(page, '2330')).toHaveCount(1)

    // 系統停止自動同步：等待期間零新請求
    await page.waitForTimeout(2500)
    expect(mock.requests).toBe(requestsAfterPair)

    // 本機增刪仍正常且不再發任何同步請求
    await addStock(page, '2317')
    await expectBadge(page, 2)
    await removeStock(page, '2317') // 未配對：直接移除
    await expectBadge(page, 1)
    expect(mock.requests).toBe(requestsAfterPair)
  })

  test('E2E-21 匯出：內容為目前追蹤項目（不含已移除墓碑）', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')
    await pair(page, 'token-export')
    await expectSynced(page)

    // 加入 ETF 0056、移除 2330（已配對 → 墓碑語意）
    await addStock(page, '0056')
    await removeStock(page, '2330')
    await expectCount(page, 1)
    await expect(row(page, '2330')).toHaveCount(0)

    // 展開備援區塊 → 匯出
    await page.locator('[data-testid="sync-backup-toggle"]').click()
    await expect(page.locator('[data-testid="sync-backup-body"]')).toBeVisible()
    await page.locator('[data-testid="sync-export-button"]').click()
    await expect(page.locator('[data-testid="sync-export-text"]')).toBeVisible()

    const content = await page.locator('[data-testid="sync-export-text"]').inputValue()
    const parsed = JSON.parse(content) as Array<{ code: string }>
    expect(parsed.map(i => i.code)).toEqual(['0056']) // 含 ETF，不含已移除的 2330
    expect(content).not.toContain('2330')
  })

  test('E2E-22 匯入：與本地清單合併且重複股票不重複加入', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330') // 本地已含 X
    await expectBadge(page, 1)

    await page.locator('[data-testid="sync-backup-toggle"]').click()
    await expect(page.locator('[data-testid="sync-backup-body"]')).toBeVisible()

    const importText = JSON.stringify([
      { code: '2330', name: '台積電', type: 'stock', addedAt: 100, updatedAt: 100 },
      { code: '2317', name: '鴻海', type: 'stock', addedAt: 101, updatedAt: 101 },
    ])
    await page.locator('[data-testid="sync-import-text"]').fill(importText)
    await page.locator('[data-testid="sync-import-submit"]').click()

    await expect(page.locator('[data-testid="sync-import-message"]')).toContainText('已合併 1 支證券')
    await expectCount(page, 2) // X 維持一筆 + Y 加入
    await expect(row(page, '2330')).toHaveCount(1) // 不重複
    await expect(row(page, '2317')).toHaveCount(1)
    await expectBadge(page, 2)
  })

  test('E2E-23 匯入格式錯誤：顯示錯誤提示且本地清單不變', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')
    await expectBadge(page, 1)

    await page.locator('[data-testid="sync-backup-toggle"]').click()
    await expect(page.locator('[data-testid="sync-backup-body"]')).toBeVisible()

    await page.locator('[data-testid="sync-import-text"]').fill('this is not json')
    await page.locator('[data-testid="sync-import-submit"]').click()

    await expect(page.locator('[data-testid="sync-import-error"]')).toContainText('匯入格式錯誤')
    await expectCount(page, 1) // 本地清單不變
    await expect(row(page, '2330')).toHaveCount(1)
    await expectBadge(page, 1)
  })

  test('E2E-email email 啟動同步：透過 Worker 建立帳號、token 自動寫入、同步成功', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')
    await expectBadge(page, 1)

    // 輸入 email → 透過 Worker 建立帳號
    await pairByEmail(page, 'test@example.com')
    await expectSynced(page)

    // Worker 被呼叫
    expect(mock.workerRequests).toBe(1)

    // kvdb 收到合併後的資料
    await waitUntil(() => cloudCodes(mock).includes('2330'))
    expect(cloudCodes(mock)).toEqual(['2330'])
    await expectBadge(page, 1)

    // Token 記住於本機
    const storedToken = await page.evaluate(k => localStorage.getItem(k), TOKEN_KEY)
    expect(storedToken).toBeTruthy()
    expect(storedToken).toContain('worker-token-')
  })

  test('E2E-email 配對碼備援：展開後可直接貼上 token 啟動', async ({ page }) => {
    const mock = createKvdbMock('ok')
    await installKvdbMock(page, mock)
    await gotoWatchlist(page)

    await addStock(page, '2330')

    // 展開配對碼輸入
    await page.locator('[data-testid="sync-token-toggle"]').click()
    await expect(page.locator('[data-testid="sync-token-input"]')).toBeVisible()

    // 直接貼上 token 啟動
    await pair(page, 'direct-token-123')
    await expectSynced(page)

    // 零 Worker 請求（直接用 token）
    expect(mock.workerRequests).toBe(0)
    await waitUntil(() => cloudCodes(mock).includes('2330'))
  })
})