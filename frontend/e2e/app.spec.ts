import { test, expect } from '@playwright/test'

test.describe('StockPayDay++ E2E', () => {
  test.describe('首頁', () => {
    test('載入首頁並顯示行事曆', async ({ page }) => {
      await page.goto('/')
      
      // 等待資料載入完成（非 loading 狀態）
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 應顯示 ViewSwitcher
      await expect(page.locator('.view-switcher')).toBeVisible()
    })

    test('根路徑使用 hash 路由（#/，GitHub Pages 相容）', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // router 使用 createWebHashHistory（GitHub Pages 靜態部署相容）
      // 根路徑 URL 為 http://host/#/
      expect(page.url()).toContain('#/')
    })

    test('Header 顯示 Logo 和功能按鈕', async ({ page }) => {
      await page.goto('/')
      
      // Logo 應可見
      await expect(page.locator('.app-logo')).toBeVisible()
      await expect(page.locator('.logo-text')).toContainText('StockPayDay++')
      
      // 追蹤清單按鈕
      await expect(page.locator('button[aria-label="追蹤清單"]')).toBeVisible()
      
      // 深色模式切換
      await expect(page.locator('.theme-toggle')).toBeVisible()
    })
  })

  test.describe('Calendar / List 視圖切換', () => {
    test('預設顯示 Calendar 視圖', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // Calendar 應可見
      await expect(page.locator('.calendar')).toBeVisible()
    })

    test('切換到 List 視圖', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 點擊 List 按鈕（使用 data-view selector）
      await page.locator('button[data-view="list"]').click()
      
      // ListView 應可見
      await expect(page.locator('.list-view')).toBeVisible()
    })

    test('切換回 Calendar 視圖', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 先切到 List
      await page.locator('button[data-view="list"]').click()
      await expect(page.locator('.list-view')).toBeVisible()
      
      // 再切回 Calendar
      await page.locator('button[data-view="calendar"]').click()
      await expect(page.locator('.calendar')).toBeVisible()
    })
  })

  test.describe('深色模式', () => {
    test('切換深色模式', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 初始應為淺色模式
      await expect(page.locator('.app-root')).not.toHaveClass(/dark/)
      
      // 點擊切換按鈕
      await page.locator('.theme-toggle').click()
      
      // 應切換為深色模式
      await expect(page.locator('.app-root')).toHaveClass(/dark/)
    })

    test('深色模式狀態持續', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 切換為深色
      await page.locator('.theme-toggle').click()
      await expect(page.locator('.app-root')).toHaveClass(/dark/)
      
      // 重新載入頁面
      await page.reload()
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 深色模式應持續
      await expect(page.locator('.app-root')).toHaveClass(/dark/)
    })
  })

  test.describe('追蹤清單', () => {
    test('點擊追蹤清單按鈕導航到 /watchlist', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 點擊追蹤清單按鈕
      await page.locator('button[aria-label="追蹤清單"]').click()
      
      // 應導航到 /watchlist
      await expect(page).toHaveURL(/\/watchlist/)
      
      // WatchlistView 應可見
      await expect(page.locator('.watchlist-view')).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('股票頁面', () => {
    test('從首頁導航到股票頁面', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 等待資料載入，點擊列表中的股票
      await page.locator('button[data-view="list"]').click()
      await expect(page.locator('.list-view')).toBeVisible()
      
      // 點擊第一支股票
      const firstStock = page.locator('.list-item').first()
      if (await firstStock.isVisible()) {
        await firstStock.click()
        await expect(page.locator('.stock-view')).toBeVisible({ timeout: 5000 })
        
        // 返回按鈕應可見
        await expect(page.locator('.back-button').first()).toBeVisible()
      }
    })

    test('返回按鈕導航回首頁', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // 切換到列表並點擊股票
      await page.locator('button[data-view="list"]').click()
      await expect(page.locator('.list-view')).toBeVisible()
      
      const firstStock = page.locator('.list-item').first()
      if (await firstStock.isVisible()) {
        await firstStock.click()
        await expect(page.locator('.stock-view')).toBeVisible({ timeout: 5000 })
        
        // 點擊返回
        await page.locator('.back-button').first().click()
        
        // 應回到首頁
        await expect(page).toHaveURL(/\/$/)
      }
    })
  })

  test.describe('RWD 響應式', () => {
    test('手機版面顯示正常', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 812 })
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      // Header 應仍可見
      await expect(page.locator('.app-header')).toBeVisible()
    })

    test('平板版面顯示正常', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await expect(page.locator('.home-view')).toBeVisible({ timeout: 10000 })
      
      await expect(page.locator('.app-header')).toBeVisible()
    })
  })
})
