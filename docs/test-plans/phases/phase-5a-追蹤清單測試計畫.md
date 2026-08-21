# 測試計畫：Phase 5a 追蹤清單

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 5a — 追蹤清單 |
| **測試類型** | 單元測試、元件測試、E2E 測試 |
| **工具** | Vitest + Vue Test Utils + Playwright |
| **BDD 對應** | `docs/bdds/stockpayday.feature` 追蹤清單章節 |

---

## 1. 測試項目

### 1.1 Composable 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| useWatchlist.add | 新增追蹤項目 | useWatchlist.spec.ts |
| useWatchlist.remove | 移除追蹤項目 | useWatchlist.spec.ts |
| useWatchlist.toggle | 切換追蹤狀態 | useWatchlist.spec.ts |
| useWatchlist.isWatched | 查詢是否已追蹤 | useWatchlist.spec.ts |
| useWatchlist.sortedItems | 排序後的追蹤清單 | useWatchlist.spec.ts |
| useWatchlist.getWatchlistUpcoming | 取得追蹤股票配息資料 | useWatchlist.spec.ts |
| useWatchlist.localStorage | 持久化儲存/讀取 | useWatchlist.spec.ts |

### 1.2 Component 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| WatchlistButton 渲染（未追蹤） | 顯示空心 ♡ | WatchlistButton.spec.ts |
| WatchlistButton 渲染（已追蹤） | 顯示實心 ♥ | WatchlistButton.spec.ts |
| WatchlistButton 點擊切換 | 切換追蹤狀態 | WatchlistButton.spec.ts |
| WatchlistButton 尺寸 | sm/md/lg 正確 | WatchlistButton.spec.ts |
| WatchlistView 渲染（空狀態） | 顯示空狀態引導 | WatchlistView.spec.ts |
| WatchlistView 渲染（有內容） | 顯示行事曆/列表 | WatchlistView.spec.ts |
| WatchlistView 模式切換 | 切換行事曆/列表 | WatchlistView.spec.ts |
| WatchlistEmpty 渲染 | 顯示引導畫面 | WatchlistEmpty.spec.ts |
| Watchlist 頁面渲染 | 顯示完整頁面 | Watchlist.spec.ts |

### 1.3 E2E 測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| 從股票詳情頁加入追蹤 | ❤️ 切換、徽章更新 | watchlist.spec.ts |
| 從列表模式加入追蹤 | ❤️ 切換、徽章更新 | watchlist.spec.ts |
| 查看追蹤清單 | 導航至 /watchlist | watchlist.spec.ts |
| 追蹤清單空狀態 | 顯示引導畫面 | watchlist.spec.ts |
| 追蹤清單搜尋加入 | 搜尋結果、加入追蹤 | watchlist.spec.ts |
| 追蹤清單模式切換 | 行事曆/列表切換 | watchlist.spec.ts |
| 追蹤清單持久化 | 刷新後仍存在 | watchlist.spec.ts |
| 導覽列徽章更新 | 數字即時更新 | watchlist.spec.ts |

---

## 2. 測試案例

### 2.1 Composable 單元測試

```typescript
// frontend/src/composables/test/useWatchlist.spec.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useWatchlist } from '../useWatchlist'

describe('useWatchlist', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('add', () => {
    it('should add stock to watchlist', () => {
      const { add, items, isWatched } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      
      expect(items.value.length).toBe(1)
      expect(items.value[0].code).toBe('2330')
      expect(items.value[0].name).toBe('台積電')
      expect(isWatched('2330')).toBe(true)
    })

    it('should not add duplicate stock', () => {
      const { add, items } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      add('2330', '台積電', 'stock')
      
      expect(items.value.length).toBe(1)
    })
  })

  describe('remove', () => {
    it('should remove stock from watchlist', () => {
      const { add, remove, items, isWatched } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      remove('2330')
      
      expect(items.value.length).toBe(0)
      expect(isWatched('2330')).toBe(false)
    })
  })

  describe('toggle', () => {
    it('should add stock when not watched', () => {
      const { toggle, items, isWatched } = useWatchlist()
      
      toggle('2330', '台積電', 'stock')
      
      expect(items.value.length).toBe(1)
      expect(isWatched('2330')).toBe(true)
    })

    it('should remove stock when watched', () => {
      const { add, toggle, items, isWatched } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      toggle('2330', '台積電', 'stock')
      
      expect(items.value.length).toBe(0)
      expect(isWatched('2330')).toBe(false)
    })
  })

  describe('isWatched', () => {
    it('should return false for unwatched stock', () => {
      const { isWatched } = useWatchlist()
      
      expect(isWatched('2330')).toBe(false)
    })

    it('should return true for watched stock', () => {
      const { add, isWatched } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      
      expect(isWatched('2330')).toBe(true)
    })
  })

  describe('sortedItems', () => {
    it('should sort by addedAt descending by default', () => {
      const { add, sortedItems } = useWatchlist()
      
      add('0050', '元大台灣50', 'etf')
      add('2330', '台積電', 'stock')
      
      expect(sortedItems.value[0].code).toBe('2330')
      expect(sortedItems.value[1].code).toBe('0050')
    })
  })

  describe('getWatchlistUpcoming', () => {
    it('should filter upcoming by watched codes', () => {
      const { add, getWatchlistUpcoming } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      
      const upcoming = [
        { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 },
        { code: '0050', name: '元大台灣50', ex_date: '2026-07-28', dividend: 2.1 },
      ]
      
      const result = getWatchlistUpcoming(upcoming)
      
      expect(result.length).toBe(1)
      expect(result[0].code).toBe('2330')
    })
  })

  describe('localStorage', () => {
    it('should persist to localStorage', () => {
      const { add } = useWatchlist()
      
      add('2330', '台積電', 'stock')
      
      const stored = JSON.parse(localStorage.getItem('stockpayday-watchlist') || '[]')
      expect(stored.length).toBe(1)
      expect(stored[0].code).toBe('2330')
    })

    it('should load from localStorage on init', () => {
      localStorage.setItem('stockpayday-watchlist', JSON.stringify([
        { code: '2330', name: '台積電', type: 'stock', addedAt: Date.now() }
      ]))
      
      const { items, isWatched } = useWatchlist()
      
      expect(items.value.length).toBe(1)
      expect(isWatched('2330')).toBe(true)
    })
  })
})
```

### 2.2 Component 整合測試

```typescript
// frontend/src/components/test/WatchlistButton.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WatchlistButton from '../WatchlistButton.vue'

describe('WatchlistButton', () => {
  it('should render empty heart when not watched', () => {
    const wrapper = mount(WatchlistButton, {
      props: { code: '2330', name: '台積電' }
    })
    
    expect(wrapper.find('button').classes()).not.toContain('watched')
    expect(wrapper.find('button').attributes('aria-label')).toBe('加入追蹤')
    expect(wrapper.find('button').attributes('aria-pressed')).toBe('false')
  })

  it('should render filled heart when watched', async () => {
    const wrapper = mount(WatchlistButton, {
      props: { code: '2330', name: '台積電' }
    })
    
    await wrapper.find('button').trigger('click')
    
    expect(wrapper.find('button').classes()).toContain('watched')
    expect(wrapper.find('button').attributes('aria-label')).toBe('移除追蹤')
    expect(wrapper.find('button').attributes('aria-pressed')).toBe('true')
  })

  it('should toggle watchlist on click', async () => {
    const wrapper = mount(WatchlistButton, {
      props: { code: '2330', name: '台積電' }
    })
    
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('button').classes()).toContain('watched')
    
    await wrapper.find('button').trigger('click')
    expect(wrapper.find('button').classes()).not.toContain('watched')
  })

  it('should apply correct size class', () => {
    const wrapper = mount(WatchlistButton, {
      props: { code: '2330', name: '台積電', size: 'lg' }
    })
    
    expect(wrapper.find('button').classes()).toContain('watchlist-btn--lg')
  })

  it('should emit toggle event', async () => {
    const wrapper = mount(WatchlistButton, {
      props: { code: '2330', name: '台積電' }
    })
    
    await wrapper.find('button').trigger('click')
    
    expect(wrapper.emitted('toggle')).toBeTruthy()
    expect(wrapper.emitted('toggle')[0]).toEqual(['2330', true])
  })
})
```

```typescript
// frontend/src/components/test/WatchlistView.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import WatchlistView from '../WatchlistView.vue'

describe('WatchlistView', () => {
  it('should show empty state when no items', () => {
    const wrapper = mount(WatchlistView)
    
    expect(wrapper.find('.watchlist-empty').exists()).toBe(true)
  })

  it('should show calendar view by default when items exist', async () => {
    // Mock useWatchlist to return items
    const wrapper = mount(WatchlistView, {
      global: {
        mocks: {
          useWatchlist: () => ({
            items: [{ code: '2330', name: '台積電' }],
            sortedItems: []
          })
        }
      }
    })
    
    expect(wrapper.find('.calendar').exists()).toBe(true)
  })

  it('should switch to list view on button click', async () => {
    const wrapper = mount(WatchlistView, {
      global: {
        mocks: {
          useWatchlist: () => ({
            items: [{ code: '2330', name: '台積電' }],
            sortedItems: []
          })
        }
      }
    })
    
    await wrapper.find('[data-view="list"]').trigger('click')
    
    expect(wrapper.find('.list-view').exists()).toBe(true)
  })
})
```

### 2.3 E2E 測試

```typescript
// frontend/tests/e2e/watchlist.spec.ts
import { test, expect } from '@playwright/test'

test.describe('追蹤清單功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('從股票詳情頁加入追蹤', async ({ page }) => {
    // 點擊行事曆上有配息的日期
    await page.click('.calendar-day.has-dividend')
    
    // 點擊該日的股票
    await page.click('.dividend-item:first-child')
    
    // 點擊追蹤按鈕
    await page.click('[data-watchlist-btn]')
    
    // 驗證按鈕變為實心
    await expect(page.locator('[data-watchlist-btn]')).toHaveClass(/watched/)
    
    // 驗證導覽列徽章更新
    await expect(page.locator('.watchlist-badge')).toContainText('1')
  })

  test('從列表模式加入追蹤', async ({ page }) => {
    // 切換至列表模式
    await page.click('[data-view="list"]')
    
    // 點擊列表項目的追蹤按鈕
    await page.click('.list-item:first-child [data-watchlist-btn]')
    
    // 驗證按鈕變為實心
    await expect(page.locator('.list-item:first-child [data-watchlist-btn]')).toHaveClass(/watched/)
  })

  test('查看追蹤清單', async ({ page }) => {
    // 先加入追蹤
    await page.click('.calendar-day.has-dividend')
    await page.click('.dividend-item:first-child')
    await page.click('[data-watchlist-btn]')
    
    // 點擊導覽列追蹤清單連結
    await page.click('.watchlist-link')
    
    // 驗證導航至 /watchlist
    await expect(page).toHaveURL('/watchlist')
    
    // 驗證頁面標題
    await expect(page.locator('.page-title')).toContainText('我的追蹤清單')
  })

  test('追蹤清單空狀態', async ({ page }) => {
    // 清除 localStorage
    await page.evaluate(() => localStorage.clear())
    
    // 導航至追蹤清單
    await page.click('.watchlist-link')
    
    // 驗證空狀態顯示
    await expect(page.locator('.watchlist-empty')).toBeVisible()
    await expect(page.locator('.empty-state-title')).toContainText('追蹤清單是空的')
  })

  test('追蹤清單搜尋加入', async ({ page }) => {
    // 導航至追蹤清單
    await page.click('.watchlist-link')
    
    // 在搜尋欄輸入
    await page.fill('#watchlist-search', '2330')
    
    // 驗證搜尋結果顯示
    await expect(page.locator('.search-results')).toBeVisible()
    await expect(page.locator('.search-result-item')).toContainText('2330')
    
    // 點擊追蹤按鈕加入
    await page.click('.search-result-item:first-child [data-watchlist-btn]')
    
    // 驗證追蹤清單更新
    await expect(page.locator('.watchlist-count')).toContainText('1')
  })

  test('追蹤清單模式切換', async ({ page }) => {
    // 先加入追蹤
    await page.click('.calendar-day.has-dividend')
    await page.click('.dividend-item:first-child')
    await page.click('[data-watchlist-btn]')
    
    // 導航至追蹤清單
    await page.click('.watchlist-link')
    
    // 驗證預設為行事曆模式
    await expect(page.locator('#calendar-view')).toBeVisible()
    
    // 切換至列表模式
    await page.click('[data-view="list"]')
    await expect(page.locator('#list-view')).toBeVisible()
    
    // 切換回行事曆模式
    await page.click('[data-view="calendar"]')
    await expect(page.locator('#calendar-view')).toBeVisible()
  })

  test('追蹤清單持久化', async ({ page }) => {
    // 先加入追蹤
    await page.click('.calendar-day.has-dividend')
    await page.click('.dividend-item:first-child')
    await page.click('[data-watchlist-btn]')
    
    // 重新整理頁面
    await page.reload()
    
    // 驗證追蹤狀態仍存在
    await expect(page.locator('.watchlist-badge')).toContainText('1')
  })

  test('導覽列徽章更新', async ({ page }) => {
    // 初始無追蹤
    await expect(page.locator('.watchlist-badge')).not.toBeVisible()
    
    // 加入追蹤
    await page.click('.calendar-day.has-dividend')
    await page.click('.dividend-item:first-child')
    await page.click('[data-watchlist-btn]')
    
    // 驗證徽章顯示
    await expect(page.locator('.watchlist-badge')).toBeVisible()
    await expect(page.locator('.watchlist-badge')).toContainText('1')
    
    // 返回首頁
    await page.click('.app-logo')
    
    // 移除追蹤
    await page.click('.calendar-day.has-dividend')
    await page.click('.dividend-item:first-child')
    await page.click('[data-watchlist-btn].watched')
    
    // 驗證徽章消失
    await expect(page.locator('.watchlist-badge')).not.toBeVisible()
  })
})
```

---

## 3. 測試覆蓋矩陣

| BDD Scenario | 單元測試 | 元件測試 | E2E 測試 | 手動測試 |
|--------------|:-------:|:-------:|:-------:|:-------:|
| 從股票詳情頁加入追蹤 | - | ✅ | ✅ | ✅ |
| 從股票詳情頁移除追蹤 | ✅ | ✅ | ✅ | ✅ |
| 從列表模式加入追蹤 | - | - | ✅ | ✅ |
| 從追蹤清單頁搜尋加入 | ✅ | - | ✅ | ✅ |
| 查看追蹤清單 | - | ✅ | ✅ | ✅ |
| 追蹤清單為空 | - | ✅ | ✅ | ✅ |
| 切換追蹤清單顯示模式 | - | ✅ | ✅ | ✅ |
| 行事曆顯示股票代號 | - | - | ✅ | ✅ |
| 列表顯示追蹤按鈕 | - | ✅ | ✅ | ✅ |
| 追蹤清單持久化 | ✅ | - | ✅ | ✅ |
| 搜尋無結果 | ✅ | - | ✅ | ✅ |
| 導覽列追蹤徽章 | - | - | ✅ | ✅ |
| 導覽列徽章為空 | - | - | ✅ | ✅ |

---

## 4. 測試環境

### 4.1 單元/元件測試

```bash
# 執行所有測試
npm run test:unit

# 執行特定檔案
npm run test:unit -- useWatchlist.spec.ts

# 觀看模式
npm run test:unit:watch
```

### 4.2 E2E 測試

```bash
# 執行所有 E2E 測試
npx playwright test

# 執行特定檔案
npx playwright test watchlist.spec.ts

# 除錯模式
npx playwright test --debug
```

---

## 5. 測試資料

### 5.1 Mock 資料

```typescript
// tests/mocks/watchlist.ts
export const mockWatchlistItems = [
  { code: '2330', name: '台積電', type: 'stock', addedAt: Date.now() },
  { code: '0056', name: '元大高股息', type: 'etf', addedAt: Date.now() - 1000 },
  { code: '0050', name: '元大台灣50', type: 'etf', addedAt: Date.now() - 2000 },
]

export const mockUpcoming = [
  { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', pay_date: '2026-08-15', dividend: 3.5 },
  { code: '0056', name: '元大高股息', type: 'etf', ex_date: '2026-07-28', pay_date: '2026-08-20', dividend: 2.1 },
  { code: '0050', name: '元大台灣50', type: 'etf', ex_date: '2026-07-30', pay_date: '2026-08-25', dividend: 1.8 },
]
```

### 5.2 localStorage Mock

```typescript
// tests/mocks/localStorage.ts
export const mockLocalStorage = {
  store: {} as Record<string, string>,
  getItem(key: string) {
    return this.store[key] || null
  },
  setItem(key: string, value: string) {
    this.store[key] = value
  },
  clear() {
    this.store = {}
  },
  removeItem(key: string) {
    delete this.store[key]
  }
}
```

---

## 6. 驗收檢查清單

### 6.1 單元測試
- [ ] useWatchlist.add 測試通過
- [ ] useWatchlist.remove 測試通過
- [ ] useWatchlist.toggle 測試通過
- [ ] useWatchlist.isWatched 測試通過
- [ ] useWatchlist.sortedItems 測試通過
- [ ] useWatchlist.getWatchlistUpcoming 測試通過
- [ ] useWatchlist localStorage 持久化測試通過

### 6.2 元件測試
- [ ] WatchlistButton 未追蹤狀態渲染正確
- [ ] WatchlistButton 已追蹤狀態渲染正確
- [ ] WatchlistButton 點擊切換正常
- [ ] WatchlistButton 尺寸 class 正確
- [ ] WatchlistView 空狀態渲染正確
- [ ] WatchlistView 有內容渲染正確
- [ ] WatchlistView 模式切換正常

### 6.3 E2E 測試
- [ ] 從股票詳情頁加入追蹤 E2E 通過
- [ ] 從列表模式加入追蹤 E2E 通過
- [ ] 查看追蹤清單 E2E 通過
- [ ] 追蹤清單空狀態 E2E 通過
- [ ] 追蹤清單搜尋加入 E2E 通過
- [ ] 追蹤清單模式切換 E2E 通過
- [ ] 追蹤清單持久化 E2E 通過
- [ ] 導覽列徽章更新 E2E 通過

### 6.4 手動測試
- [ ] 手機版追蹤按鈕可正常點擊
- [ ] 手機版追蹤清單頁面可正常顯示
- [ ] 手機版搜尋欄可正常使用
- [ ] 深色模式下所有元件樣式正常

---

## 📝 備註

- 測試環境需設定 `localStorage` mock
- E2E 測試需先啟動 dev server
- 追蹤清單功能為純前端，無需 mock API
