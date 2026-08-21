# 測試計畫：Phase 8 優化打磨（RWD + 深色模式）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 8 — 優化打磨 |
| **測試類型** | E2E 測試、視覺測試、手動測試 |
| **工具** | Playwright、手動測試 |
| **BDD 對應** | RWD 響應式設計、深色模式 |

---

## 1. 測試項目

### 1.1 RWD 響應式設計測試

| 測試項目 | 預期結果 | 測試工具 |
|----------|----------|----------|
| 手機版（< 768px） | 正常顯示 | Playwright |
| 平板版（768-1024px） | 正常顯示 | Playwright |
| 桌機版（> 1024px） | 正常顯示 | Playwright |
| 視窗大小改變 | 佈局即時調整 | Playwright |

### 1.2 深色模式測試

| 測試項目 | 預期結果 | 測試工具 |
|----------|----------|----------|
| 系統偏好偵測 | 自動套用 | Playwright |
| 手動切換 | 即時切換 | Playwright |
| 主題持久化 | localStorage | Playwright |
| 視覺效果 | 可閱讀 | 手動測試 |

---

## 2. 測試案例

### 2.1 RWD 測試

```typescript
// frontend/tests/e2e/rwd.spec.ts
import { test, expect } from '@playwright/test'

test.describe('RWD 響應式設計', () => {
  test.describe('手機版（< 768px）', () => {
    test.use({ viewport: { width: 375, height: 812 } })
    
    test('行事曆正常顯示', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.calendar')).toBeVisible()
    })
    
    test('列表可正常捲動', async ({ page }) => {
      await page.goto('/')
      await page.click('text=列表')
      await expect(page.locator('.list-view')).toBeVisible()
      
      // 測試捲動
      await page.evaluate(() => {
        document.querySelector('.list-view')?.scrollTo(0, 1000)
      })
    })
    
    test('搜尋欄可正常使用', async ({ page }) => {
      await page.goto('/')
      await page.fill('input[placeholder*="搜尋"]', '2330')
      await expect(page.locator('.search-result')).toBeVisible()
    })
    
    test('導航功能正常', async ({ page }) => {
      await page.goto('/')
      await page.click('.list-item >> text=2330')
      await expect(page).toHaveURL(/\/stock\/2330/)
      
      await page.click('text=返回')
      await expect(page).toHaveURL('/')
    })
  })
  
  test.describe('平板版（768-1024px）', () => {
    test.use({ viewport: { width: 768, height: 1024 } })
    
    test('佈局適中', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.calendar')).toBeVisible()
    })
    
    test('所有功能可正常使用', async ({ page }) => {
      await page.goto('/')
      
      // 測試模式切換
      await page.click('text=列表')
      await expect(page.locator('.list-view')).toBeVisible()
      
      // 測試搜尋
      await page.fill('input[placeholder*="搜尋"]', '2330')
      await expect(page.locator('.search-result')).toBeVisible()
    })
  })
  
  test.describe('桌機版（> 1024px）', () => {
    test.use({ viewport: { width: 1920, height: 1080 } })
    
    test('佈局完整', async ({ page }) => {
      await page.goto('/')
      await expect(page.locator('.calendar')).toBeVisible()
    })
    
    test('充分利用空間', async ({ page }) => {
      await page.goto('/')
      
      // 驗證行事曆格子寬度合理
      const calendarWidth = await page.locator('.calendar').evaluate(el => el.clientWidth)
      expect(calendarWidth).toBeGreaterThan(800)
    })
  })
  
  test.describe('動態調整', () => {
    test('視窗大小改變時佈局即時調整', async ({ page }) => {
      await page.goto('/')
      
      // 初始為桌機版
      await page.setViewportSize({ width: 1920, height: 1080 })
      await expect(page.locator('.calendar')).toBeVisible()
      
      // 改為手機版
      await page.setViewportSize({ width: 375, height: 812 })
      await expect(page.locator('.calendar')).toBeVisible()
      
      // 改回桌機版
      await page.setViewportSize({ width: 1920, height: 1080 })
      await expect(page.locator('.calendar')).toBeVisible()
    })
  })
})
```

### 2.2 深色模式測試

```typescript
// frontend/tests/e2e/dark-mode.spec.ts
import { test, expect } from '@playwright/test'

test.describe('深色模式', () => {
  test.describe('系統偏好偵測', () => {
    test.use({ colorScheme: 'dark' })
    
    test('自動套用深色模式', async ({ page }) => {
      await page.goto('/')
      
      // 驗證 html 有 dark class
      await expect(page.locator('html')).toHaveClass(/dark/)
    })
    
    test('深色模式視覺效果', async ({ page }) => {
      await page.goto('/')
      
      // 驗證背景色為深色
      const bgColor = await page.evaluate(() => {
        return getComputedStyle(document.body).backgroundColor
      })
      
      // 深色模式背景應該是深色
      expect(bgColor).not.toBe('rgb(255, 255, 255)')
    })
  })
  
  test.use({ colorScheme: 'light' })
  
  test.describe('系統偏好偵測（淺色）', () => {
    test('自動套用淺色模式', async ({ page }) => {
      await page.goto('/')
      
      // 驗證 html 沒有 dark class
      await expect(page.locator('html')).not.toHaveClass(/dark/)
    })
  })
  
  test.describe('手動切換', () => {
    test('切換至深色模式', async ({ page }) => {
      await page.goto('/')
      
      // 點擊切換按鈕
      await page.click('[data-theme-toggle]')
      
      // 驗證切換成功
      await expect(page.locator('html')).toHaveClass(/dark/)
    })
    
    test('切換至淺色模式', async ({ page }) => {
      await page.goto('/')
      
      // 先切換到深色
      await page.click('[data-theme-toggle]')
      await expect(page.locator('html')).toHaveClass(/dark/)
      
      // 再切換回淺色
      await page.click('[data-theme-toggle]')
      await expect(page.locator('html')).not.toHaveClass(/dark/)
    })
    
    test('主題持久化', async ({ page }) => {
      await page.goto('/')
      
      // 切換到深色模式
      await page.click('[data-theme-toggle]')
      await expect(page.locator('html')).toHaveClass(/dark/)
      
      // 重新載入頁面
      await page.reload()
      
      // 驗證主題保持
      await expect(page.locator('html')).toHaveClass(/dark/)
    })
  })
  
  test.describe('視覺效果', () => {
    test.use({ colorScheme: 'dark' })
    
    test('文字可閱讀', async ({ page }) => {
      await page.goto('/')
      
      // 驗證文字顏色對比度
      const textColor = await page.evaluate(() => {
        const el = document.querySelector('.calendar-header')
        return el ? getComputedStyle(el).color : null
      })
      
      expect(textColor).not.toBe('rgb(0, 0, 0)') // 不應該是黑色
    })
    
    test('按鈕可辨識', async ({ page }) => {
      await page.goto('/')
      
      // 驗證按鈕可見
      await expect(page.locator('[data-theme-toggle]')).toBeVisible()
    })
  })
})
```

---

## 3. 視覺回歸測試（選用）

### 3.1 Playwright 截圖比較

```typescript
// frontend/tests/e2e/visual.spec.ts
import { test, expect } from '@playwright/test'

test.describe('視覺回歸測試', () => {
  test('行事曆截圖比較', async ({ page }) => {
    await page.goto('/')
    
    // 截圖
    await expect(page).toHaveScreenshot('calendar-light.png')
  })
  
  test('深色模式截圖比較', async ({ page }) => {
    await page.use({ colorScheme: 'dark' })
    await page.goto('/')
    
    // 截圖
    await expect(page).toHaveScreenshot('calendar-dark.png')
  })
  
  test('手機版截圖比較', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto('/')
    
    // 截圖
    await expect(page).toHaveScreenshot('calendar-mobile.png')
  })
})
```

---

## 4. 手動測試清單

### 4.1 RWD 手動測試

| 測試項目 | 裝置 | 預期結果 | 通過 |
|----------|------|----------|:----:|
| 行事曆顯示 | iPhone | 正常顯示 | ☐ |
| 行事曆顯示 | iPad | 正常顯示 | ☐ |
| 行事曆顯示 | 桌機 | 正常顯示 | ☐ |
| 列表顯示 | iPhone | 可捲動 | ☐ |
| 列表顯示 | iPad | 可捲動 | ☐ |
| 列表顯示 | 桌機 | 可捲動 | ☐ |
| 搜尋功能 | iPhone | 可正常使用 | ☐ |
| 搜尋功能 | iPad | 可正常使用 | ☐ |
| 搜尋功能 | 桌機 | 可正常使用 | ☐ |
| 導航功能 | iPhone | 正常導航 | ☐ |
| 導航功能 | iPad | 正常導航 | ☐ |
| 導航功能 | 桌機 | 正常導航 | ☐ |

### 4.2 深色模式手動測試

| 測試項目 | 預期結果 | 通過 |
|----------|----------|:----:|
| 系統深色模式 | 自動套用 | ☐ |
| 系統淺色模式 | 自動套用 | ☐ |
| 手動切換 | 即時切換 | ☐ |
| 主題持久化 | 重新載入保持 | ☐ |
| 文字可閱讀 | 對比度足夠 | ☐ |
| 按鈕可辨識 | 可清楚看到 | ☐ |
| 行事曆顯示 | 深色模式正常 | ☐ |
| 列表顯示 | 深色模式正常 | ☐ |
| 歷史頁面 | 深色模式正常 | ☐ |

---

## 5. 測試執行

```bash
# 執行 Playwright 測試
cd frontend && npx playwright test tests/e2e/rwd.spec.ts
npx playwright test tests/e2e/dark-mode.spec.ts

# 執行視覺回歸測試
npx playwright test tests/e2e/visual.spec.ts --update-screenshots

# 比較截圖
npx playwright test tests/e2e/visual.spec.ts
```

---

## 6. 驗收標準

### 6.1 RWD 測試

| 標準 | 目標 |
|------|------|
| 手機版（< 768px） | 所有功能正常 |
| 平板版（768-1024px） | 所有功能正常 |
| 桌機版（> 1024px） | 所有功能正常 |
| 動態調整 | 佈局即時調整 |

### 6.2 深色模式測試

| 標準 | 目標 |
|------|------|
| 系統偏好偵測 | 自動套用正確主題 |
| 手動切換 | 即時切換無延遲 |
| 主題持久化 | 重新載入保持 |
| 視覺效果 | 文字可閱讀、按鈕可辨識 |

### 6.3 整體驗收

| 標準 | 目標 |
|------|------|
| E2E 測試通過率 | 100% |
| 手動測試通過率 | 100% |
| 視覺回歸 | 無明顯差異 |
| 使用者體驗 | 流暢、舒適 |

---

## 7. 測試注意事項

1. **多裝置測試** — 使用真實裝置或模擬器測試
2. **多瀏覽器測試** — Chrome、Firefox、Safari
3. **色彩對比** — 確保深色模式下文字可閱讀
4. **效能測試** — 響應式佈局不應影響效能
5. **使用者回饋** — 收集小群體使用者的回饋
