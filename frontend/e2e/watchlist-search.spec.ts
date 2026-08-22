import { test, expect } from '@playwright/test'

/**
 * E2E：功能 001 追蹤任意股票（含尚未公布配息的股票）
 *
 * 真實資料（api/securities-index.json, api/upcoming.json）：
 * - 2330 台積電：在 securities-index，不在 upcoming → 無配息
 * - 2317 鴻海：在 securities-index，不在 upcoming
 * - 2458 義隆：在 securities-index + 有詳情檔（不在 upcoming）→ 導航回歸用
 * - XXXXXX：不存在 → 無結果提示
 */
test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await page.evaluate(() => localStorage.clear())
  await page.reload()
  await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
})

test.describe('導覽列搜尋結果直接追蹤', () => {
  test('搜尋結果每列顯示 ❤️，未追蹤為空心', async ({ page }) => {
    await page.fill('.search-input', '2330')
    await expect(page.locator('.search-results')).toBeVisible()

    const heart = page.locator('[data-testid="heart-2330"]')
    await expect(heart).toBeVisible()
    await expect(heart).not.toHaveClass(/watched/)
    await expect(heart).toHaveAttribute('aria-pressed', 'false')
  })

  test('點 ❤️ 加入：實心、徽章 +1、URL 不變、下拉保持顯示', async ({ page }) => {
    await page.fill('.search-input', '2330')
    await expect(page.locator('[data-testid="heart-2330"]')).toBeVisible()

    await page.locator('[data-testid="heart-2330"]').click()

    await expect(page.locator('[data-testid="heart-2330"]')).toHaveClass(/watched/)
    await expect(page.locator('.watchlist-badge')).toHaveText('1')
    // ❤️ 不觸發導航
    await expect(page).toHaveURL(/#\/$/)
    // 下拉保持顯示（須撐過 input blur + setTimeout(150ms) 窗口）
    await page.waitForTimeout(400)
    await expect(page.locator('.search-results')).toBeVisible()
  })

  test('再次點 ❤️ 移除：空心、徽章消失', async ({ page }) => {
    await page.fill('.search-input', '2330')
    await page.locator('[data-testid="heart-2330"]').click()
    await expect(page.locator('.watchlist-badge')).toHaveText('1')

    await page.locator('[data-testid="heart-2330"]').click()

    await expect(page.locator('[data-testid="heart-2330"]')).not.toHaveClass(/watched/)
    await expect(page.locator('.watchlist-badge')).toBeHidden()
  })

  test('點名稱導航至詳情頁，詳情頁 ❤️ 與搜尋結果一致（回歸）', async ({ page }) => {
    await page.fill('.search-input', '2458')
    await expect(page.locator('[data-testid="heart-2458"]')).toBeVisible()

    // 先從搜尋結果追蹤
    await page.locator('[data-testid="heart-2458"]').click()
    await expect(page.locator('[data-testid="heart-2458"]')).toHaveClass(/watched/)

    // 點結果名稱 → 導航
    await page.locator('.search-result-item:has-text("2458") .result-main').click()
    await expect(page).toHaveURL(/\/stock\/2458/)
    await expect(page.locator('.stock-view')).toBeVisible({ timeout: 5000 })

    // 詳情頁 ❤️ 與搜尋結果一致（實心、徽章不變）
    await expect(page.locator('[data-testid="heart-2458"]')).toHaveClass(/watched/)
    await expect(page.locator('.watchlist-badge')).toHaveText('1')
  })

  test('重整頁面後追蹤狀態保持（持久化）', async ({ page }) => {
    await page.fill('.search-input', '2330')
    await page.locator('[data-testid="heart-2330"]').click()
    await expect(page.locator('[data-testid="heart-2330"]')).toHaveClass(/watched/)

    await page.reload()
    await page.fill('.search-input', '2330')

    await expect(page.locator('[data-testid="heart-2330"]')).toHaveClass(/watched/)
    await expect(page.locator('.watchlist-badge')).toHaveText('1')
  })
})

test.describe('追蹤尚未公布配息的股票', () => {
  test('追蹤 2330（不在 upcoming）→ 追蹤清單顯示「無近期配息」', async ({ page }) => {
    await page.fill('.search-input', '2330')
    await page.locator('[data-testid="heart-2330"]').click()
    await expect(page.locator('[data-testid="heart-2330"]')).toHaveClass(/watched/)

    await page.locator('button[aria-label="追蹤清單"]').click()
    await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 5000 })

    await expect(page.locator('body')).toContainText('2330')
    await expect(page.locator('.item-no-dividend')).toHaveText('無近期配息')
  })
})

test.describe('追蹤清單頁常駐搜尋欄', () => {
  test('頂部搜尋欄：代號/名稱搜尋、結果含 ❤️、點 ❤️ 清單立即更新', async ({ page }) => {
    await page.locator('button[aria-label="追蹤清單"]').click()
    await expect(page.locator('[data-testid="watchlist-search"]')).toBeVisible()

    const wlInput = page.locator('[data-testid="watchlist-search"] .search-input')

    // 代號搜尋
    await wlInput.fill('2330')
    await expect(page.locator('[data-testid="heart-2330"]')).toBeVisible()

    // 名稱搜尋
    await wlInput.fill('台積')
    await expect(page.locator('.search-result-item:has-text("台積電")')).toBeVisible()

    // 點 ❤️ 加入 → 清單立即更新 + 徽章 +1
    await page.locator('[data-testid="heart-2330"]').click()
    await expect(page.locator('.watchlist-badge')).toHaveText('1')
    await expect(page.locator('.watchlist-count')).toHaveText(/已追蹤 1 支證券/)
  })

  test('空狀態時搜尋欄仍可用：加入後脫離空狀態', async ({ page }) => {
    await page.locator('button[aria-label="追蹤清單"]').click()
    await expect(page.locator('.watchlist-empty')).toBeVisible()

    const wlInput = page.locator('[data-testid="watchlist-search"] .search-input')
    await wlInput.fill('2317')
    await expect(page.locator('[data-testid="heart-2317"]')).toBeVisible()

    await page.locator('[data-testid="heart-2317"]').click()

    await expect(page.locator('.watchlist-empty')).toBeHidden()
    await expect(page.locator('.watchlist-count')).toHaveText(/已追蹤 1 支證券/)
    await expect(page.locator('body')).toContainText('鴻海')
  })

  test('搜尋無結果顯示「找不到符合的證券」', async ({ page }) => {
    await page.locator('button[aria-label="追蹤清單"]').click()

    await page.fill('[data-testid="watchlist-search"] .search-input', 'XXXXXX')

    await expect(page.locator('.no-results')).toContainText('找不到符合的證券')
  })
})

test.describe('手機版（< 768px）', () => {
  test('追蹤清單頁搜尋欄可用、❤️ 44px 觸控目標可正常點擊', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')
    await page.locator('button[aria-label="追蹤清單"]').click()
    await expect(page.locator('[data-testid="watchlist-search"]')).toBeVisible()

    const wlInput = page.locator('[data-testid="watchlist-search"] .search-input')
    await wlInput.fill('2330')
    await expect(page.locator('[data-testid="heart-2330"]')).toBeVisible()

    // 觸控目標 ≥ 44×44px
    const box = await page.locator('[data-testid="heart-2330"]').boundingBox()
    expect(box!.width).toBeGreaterThanOrEqual(44)
    expect(box!.height).toBeGreaterThanOrEqual(44)

    await page.locator('[data-testid="heart-2330"]').click()
    await expect(page.locator('.watchlist-badge')).toHaveText('1')
  })
})