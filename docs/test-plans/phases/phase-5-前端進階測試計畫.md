# 測試計畫：Phase 5 前端進階（單股歷史 + 搜尋）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 5 — 前端進階 |
| **測試類型** | 單元測試、元件測試、E2E 測試 |
| **工具** | Vitest + Vue Test Utils + Playwright |
| **BDD 對應** | 單股歷史頁面、搜尋功能 |

---

## 1. 測試項目

### 1.1 Composable 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| useStock | 載入單股資料 | useStock.spec.ts |
| useSearch | 搜尋功能 | useSearch.spec.ts |
| useSearch.filterByCode | 代號搜尋 | useSearch.spec.ts |
| useSearch.filterByName | 名稱搜尋 | useSearch.spec.ts |

### 1.2 Component 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| StockDetail 渲染 | 顯示股票資訊 | StockDetail.spec.ts |
| StockDetail 歷史表格 | 正確顯示歷史 | StockDetail.spec.ts |
| SearchBar 渲染 | 顯示搜尋欄 | SearchBar.spec.ts |
| SearchBar 即時搜尋 | 輸入時篩選 | SearchBar.spec.ts |
| SearchBar 結果點擊 | 點擊導航 | SearchBar.spec.ts |
| BackButton 導航 | 返回首頁 | BackButton.spec.ts |

### 1.3 E2E 測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| 從列表導航至歷史 | URL 變更、顯示歷史 | stock-detail.spec.ts |
| 從行事曆導航至歷史 | URL 變更、顯示歷史 | stock-detail.spec.ts |
| 搜尋股票 | 顯示搜尋結果 | search.spec.ts |
| 點擊搜尋結果 | 導航至歷史頁面 | search.spec.ts |
| 返回首頁 | 回到首頁 | navigation.spec.ts |

---

## 2. 測試案例

### 2.1 Composable 單元測試

```typescript
// frontend/src/composables/test/useStock.spec.ts
import { describe, it, expect } from 'vitest'
import { useStock } from '../useStock'

describe('useStock', () => {
  it('should load stock data by code', async () => {
    const { stock, loading, error } = useStock('2330')
    
    expect(loading.value).toBe(true)
    
    await waitForNextTick()
    
    expect(loading.value).toBe(false)
    expect(stock.value).toBeDefined()
    expect(stock.value?.code).toBe('2330')
  })
  
  it('should handle stock not found', async () => {
    const { stock, error } = useStock('XXXXX')
    
    await waitForNextTick()
    
    expect(stock.value).toBeNull()
    expect(error.value).toBeDefined()
  })
  
  it('should load dividend history', async () => {
    const { stock } = useStock('2330')
    
    await waitForNextTick()
    
    expect(stock.value?.history).toBeDefined()
    expect(Array.isArray(stock.value?.history)).toBe(true)
  })
})

// frontend/src/composables/test/useSearch.spec.ts
import { describe, it, expect } from 'vitest'
import { useSearch } from '../useSearch'

describe('useSearch', () => {
  it('should search by stock code', async () => {
    const { query, results } = useSearch()
    
    query.value = '2330'
    await waitForNextTick()
    
    expect(results.value.length).toBeGreaterThan(0)
    expect(results.value.some(r => r.code === '2330')).toBe(true)
  })
  
  it('should search by stock name', async () => {
    const { query, results } = useSearch()
    
    query.value = '台積'
    await waitForNextTick()
    
    expect(results.value.length).toBeGreaterThan(0)
    expect(results.value.some(r => r.name.includes('台積'))).toBe(true)
  })
  
  it('should return empty for no match', async () => {
    const { query, results } = useSearch()
    
    query.value = 'XXXXX'
    await waitForNextTick()
    
    expect(results.value.length).toBe(0)
  })
  
  it('should clear results when query is empty', async () => {
    const { query, results } = useSearch()
    
    query.value = '2330'
    await waitForNextTick()
    expect(results.value.length).toBeGreaterThan(0)
    
    query.value = ''
    await waitForNextTick()
    expect(results.value.length).toBe(0)
  })
})
```

### 2.2 Component 整合測試

```typescript
// frontend/src/components/test/StockDetail.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StockDetail from '../StockDetail.vue'

describe('StockDetail', () => {
  const mockStock = {
    code: '2330',
    name: '台積電',
    history: [
      { year: 2026, ex_date: '2026-07-25', dividend: 3.5 },
      { year: 2025, ex_date: '2025-07-18', dividend: 3.2 }
    ]
  }
  
  it('renders stock info', () => {
    const wrapper = mount(StockDetail, {
      props: { stock: mockStock }
    })
    
    expect(wrapper.find('.stock-code').text()).toBe('2330')
    expect(wrapper.find('.stock-name').text()).toBe('台積電')
  })
  
  it('renders history table', () => {
    const wrapper = mount(StockDetail, {
      props: { stock: mockStock }
    })
    
    const rows = wrapper.findAll('.history-row')
    expect(rows.length).toBe(2)
  })
  
  it('sorts history by year descending', () => {
    const wrapper = mount(StockDetail, {
      props: { stock: mockStock }
    })
    
    const rows = wrapper.findAll('.history-row')
    expect(rows[0].text()).toContain('2026')
    expect(rows[1].text()).toContain('2025')
  })
  
  it('emits back-click when clicking back button', async () => {
    const wrapper = mount(StockDetail, {
      props: { stock: mockStock }
    })
    
    await wrapper.find('.back-button').trigger('click')
    
    expect(wrapper.emitted('back-click')).toBeTruthy()
  })
  
  it('shows loading state', () => {
    const wrapper = mount(StockDetail, {
      props: { stock: null, loading: true }
    })
    
    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
  })
  
  it('shows error state', () => {
    const wrapper = mount(StockDetail, {
      props: { stock: null, error: '找不到資料' }
    })
    
    expect(wrapper.find('.error-message').text()).toContain('找不到資料')
  })
})

// frontend/src/components/test/SearchBar.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchBar from '../SearchBar.vue'

describe('SearchBar', () => {
  it('renders search input', () => {
    const wrapper = mount(SearchBar)
    
    expect(wrapper.find('input').exists()).toBe(true)
  })
  
  it('emits input event when typing', async () => {
    const wrapper = mount(SearchBar)
    
    await wrapper.find('input').setValue('2330')
    
    expect(wrapper.emitted('input')).toBeTruthy()
    expect(wrapper.emitted('input')![0]).toEqual(['2330'])
  })
  
  it('displays search results', async () => {
    const results = [
      { code: '2330', name: '台積電' }
    ]
    const wrapper = mount(SearchBar, {
      props: { results }
    })
    
    expect(wrapper.find('.search-results').exists()).toBe(true)
    expect(wrapper.findAll('.search-result-item').length).toBe(1)
  })
  
  it('emits select event when clicking result', async () => {
    const results = [
      { code: '2330', name: '台積電' }
    ]
    const wrapper = mount(SearchBar, {
      props: { results }
    })
    
    await wrapper.find('.search-result-item').trigger('click')
    
    expect(wrapper.emitted('select')).toBeTruthy()
  })
  
  it('shows no results message', async () => {
    const wrapper = mount(SearchBar, {
      props: { results: [], query: 'XXXXX' }
    })
    
    expect(wrapper.find('.no-results').text()).toContain('找不到')
  })
})

// frontend/src/components/test/BackButton.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BackButton from '../BackButton.vue'

describe('BackButton', () => {
  it('renders back button', () => {
    const wrapper = mount(BackButton)
    
    expect(wrapper.find('.back-button').exists()).toBe(true)
    expect(wrapper.find('.back-button').text()).toContain('返回')
  })
  
  it('emits click event', async () => {
    const wrapper = mount(BackButton)
    
    await wrapper.find('.back-button').trigger('click')
    
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

---

## 3. E2E 測試

```typescript
// frontend/tests/e2e/stock-detail.spec.ts
import { test, expect } from '@playwright/test'

test.describe('單股歷史頁面', () => {
  test('從列表導航至歷史頁面', async ({ page }) => {
    await page.goto('/')
    await page.click('text=列表')
    await page.click('.list-item >> text=2330')
    
    await expect(page).toHaveURL(/\/stock\/2330/)
    await expect(page.locator('.stock-name')).toContainText('台積電')
  })
  
  test('從行事曆導航至歷史頁面', async ({ page }) => {
    await page.goto('/')
    await page.click('[data-date="2026-07-25"]')
    await page.click('.stock-item >> text=2330')
    
    await expect(page).toHaveURL(/\/stock\/2330/)
  })
  
  test('顯示歷史配息表格', async ({ page }) => {
    await page.goto('/stock/2330')
    
    await expect(page.locator('.history-table')).toBeVisible()
    await expect(page.locator('.history-row').first()).toBeVisible()
  })
  
  test('返回按鈕回首頁', async ({ page }) => {
    await page.goto('/stock/2330')
    await page.click('text=返回')
    
    await expect(page).toHaveURL('/')
  })
})

// frontend/tests/e2e/search.spec.ts
import { test, expect } from '@playwright/test'

test.describe('搜尋功能', () => {
  test('搜尋股票代號', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', '2330')
    
    await expect(page.locator('.search-result')).toContainText('台積電')
  })
  
  test('搜尋股票名稱', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', '台積')
    
    await expect(page.locator('.search-result')).toContainText('2330')
  })
  
  test('點擊搜尋結果導航至歷史頁面', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', '2330')
    await page.click('.search-result')
    
    await expect(page).toHaveURL(/\/stock\/2330/)
  })
  
  test('搜尋無結果顯示提示', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', 'XXXXX')
    
    await expect(page.locator('.no-results')).toBeVisible()
  })
})
```

---

## 4. 測試執行

```bash
# 執行 Vitest 測試
cd frontend && npm run test:unit

# 執行 Playwright E2E 測試
cd frontend && npx playwright test

# 執行特定 E2E 測試
npx playwright test tests/e2e/stock-detail.spec.ts

# 互動模式（除錯）
npx playwright test --debug
```

---

## 5. 驗收標準

| 標準 | 目標 |
|------|------|
| Composable 測試通過率 | 100% |
| Component 測試通過率 | 100% |
| E2E 測試通過率 | 100% |
| 測試覆蓋率 | > 70% |
| 導航功能 | 正確導航 |
| 搜尋功能 | 即時搜尋 |
| 返回功能 | 正確回首頁 |
| 載入狀態 | 正確顯示 |
| 錯誤處理 | 正確顯示 |

---

## 6. 測試資料

```typescript
// frontend/src/__mocks__/api.ts
export const mockStockDetail = {
  code: '2330',
  name: '台積電',
  history: [
    { year: 2026, ex_date: '2026-07-25', dividend: 3.5 },
    { year: 2025, ex_date: '2025-07-18', dividend: 3.2 },
    { year: 2024, ex_date: '2024-06-12', dividend: 2.9 }
  ]
}

export const mockSecuritiesIndex = [
  { code: '2330', name: '台積電' },
  { code: '0050', name: '元大台灣50' },
  { code: '0056', name: '元大高股息' }
]
```
