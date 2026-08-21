# 測試計畫：股市配息行事曆（StockPayDay++）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **功能名稱** | 股市配息行事曆 |
| **對應 BDD** | `docs/bdds/stockpayday.feature` |
| **技術棧** | Python 3.11+ · Vue 3 · Vite 5 · Tailwind CSS 3 |
| **測試範圍** | 單元測試、整合測試、E2E 測試 |

---

## 1. 測試策略

### 1.1 測試金字塔

```
        ┌─────────────┐
        │   E2E 測試   │  ← Playwright（手動或自動）
        ├─────────────┤
        │  整合測試    │  ← Python pytest + Vue Test Utils
        ├─────────────┤
        │  單元測試    │  ← Python pytest + Vitest
        └─────────────┘
```

### 1.2 測試工具

| 層級 | 工具 | 說明 |
|------|------|------|
| Python 單元測試 | pytest | 爬蟲、處理器邏輯 |
| Python 整合測試 | pytest | 爬蟲 + 資料儲存流程 |
| Vue 單元測試 | Vitest | Composable、Store |
| Vue 整合測試 | Vue Test Utils + Vitest | Component |
| E2E 測試 | Playwright | 完整使用者流程 |

---

## 2. 單元測試

### 2.1 Python — 爬蟲模組

#### crawler/sources/test_twse_stock.py

```python
"""個股爬蟲單元測試"""
import pytest
from sources.twse_stock import TWSEStockCrawler, parse_dividend_record

class TestTWSEStockCrawler:
    """TWSE 個股爬蟲測試"""
    
    def test_parse_dividend_record(self):
        """測試配息紀錄解析"""
        raw = {
            "stock_code": "2330",
            "stock_name": "台積電",
            "year": 2026,
            "quarter": 2,
            "ex_date": "2026-07-25",
            "cash_dividend": 3.5
        }
        result = parse_dividend_record(raw)
        assert result["code"] == "2330"
        assert result["name"] == "台積電"
        assert result["cash_dividend"] == 3.5
    
    def test_parse_dividend_record_missing_fields(self):
        """測試欄位缺失時的處理"""
        raw = {"stock_code": "2330"}
        result = parse_dividend_record(raw)
        assert result["code"] == "2330"
        assert result["cash_dividend"] == 0
```

#### crawler/sources/test_twse_etf.py

```python
"""ETF 爬蟲單元測試"""
import pytest
from sources.twse_etf import TWSEETFCrawler

class TestTWSEETFCrawler:
    """TWSE ETF 爬蟲測試"""
    
    def test_fetch_etf_list(self):
        """測試 ETF 列表抓取"""
        crawler = TWSEETFCrawler()
        # TODO: 實作測試
        pass
    
    def test_fetch_etf_dividend(self):
        """測試單支 ETF 配息抓取"""
        crawler = TWSEETFCrawler()
        # TODO: 實作測試
        pass
```

### 2.2 Python — 處理器模組

#### processor/test_generate_api.py

```python
"""處理器單元測試"""
import pytest
import json
import tempfile
from pathlib import Path
from generate_api import generate_upcoming, generate_securities_index

class TestGenerateAPI:
    """API 資料產生測試"""
    
    def test_generate_upcoming_filters_future(self):
        """測試 upcoming.json 只包含未來配息"""
        # TODO: 準備測試資料
        # TODO: 執行 generate_upcoming
        # TODO: 驗證只包含 ex_date >= 今天
        pass
    
    def test_generate_securities_index(self):
        """測試 securities-index.json 包含所有證券"""
        # TODO: 實作測試
        pass
```

### 2.3 Vue — Composable

#### frontend/src/composables/test_useCalendar.ts

```typescript
/**Composable 單元測試 */
import { describe, it, expect } from 'vitest'
import { useCalendar } from './useCalendar'

describe('useCalendar', () => {
  it('should generate calendar days for current month', () => {
    const { days, currentMonth } = useCalendar()
    expect(days.value.length).toBeGreaterThan(0)
    expect(currentMonth.value).toBeDefined()
  })
  
  it('should navigate to previous month', () => {
    const { currentMonth, prevMonth } = useCalendar()
    const before = currentMonth.value
    prevMonth()
    expect(currentMonth.value).not.toBe(before)
  })
  
  it('should navigate to next month', () => {
    const { currentMonth, nextMonth } = useCalendar()
    const before = currentMonth.value
    nextMonth()
    expect(currentMonth.value).not.toBe(before)
  })
})
```

---

## 3. 整合測試

### 3.1 Python — 爬蟲整合測試

#### crawler/test_integration.py

```python
"""爬蟲整合測試"""
import pytest
import tempfile
from pathlib import Path
from fetch import main as run_crawler

class TestCrawlerIntegration:
    """爬蟲整合測試"""
    
    def test_full_crawl_stock(self):
        """測試完整個股爬蟲流程"""
        # TODO: 使用 mock 或真實 API
        # TODO: 驗證 data/stocks/ 有資料
        pass
    
    def test_full_crawl_etf(self):
        """測試完整 ETF 爬蟲流程"""
        # TODO: 實作測試
        pass
    
    def test_crawl_and_process(self):
        """測試爬蟲 + 處理器整合"""
        # TODO: 執行爬蟲
        # TODO: 執行處理器
        # TODO: 驗證 api/ 有正確資料
        pass
```

### 3.2 Vue — Component 整合測試

#### frontend/src/components/test/Calendar.spec.ts

```typescript
/**Calendar 元件整合測試 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Calendar from '../Calendar.vue'

describe('Calendar', () => {
  it('renders calendar grid', () => {
    const wrapper = mount(Calendar, {
      props: {
        upcoming: [
          { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
        ]
      }
    })
    expect(wrapper.find('.calendar-grid').exists()).toBe(true)
  })
  
  it('highlights dates with dividends', () => {
    const wrapper = mount(Calendar, {
      props: {
        upcoming: [
          { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
        ]
      }
    })
    expect(wrapper.find('[data-date="2026-07-25"]').classes()).toContain('has-dividend')
  })
  
  it('emits date-click event', async () => {
    const wrapper = mount(Calendar, {
      props: {
        upcoming: [
          { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
        ]
      }
    })
    await wrapper.find('[data-date="2026-07-25"]').trigger('click')
    expect(wrapper.emitted('date-click')).toBeTruthy()
  })
})
```

#### frontend/src/components/test/ListView.spec.ts

```typescript
/**ListView 元件整合測試 */
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ListView from '../ListView.vue'

describe('ListView', () => {
  it('renders dividend list sorted by date', () => {
    const wrapper = mount(ListView, {
      props: {
        upcoming: [
          { code: '0056', name: '元大高股息', ex_date: '2026-07-20', dividend: 1.8 },
          { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
        ]
      }
    })
    const items = wrapper.findAll('.list-item')
    expect(items[0].text()).toContain('07-20')
    expect(items[1].text()).toContain('07-25')
  })
  
  it('emits stock-click event', async () => {
    const wrapper = mount(ListView, {
      props: {
        upcoming: [
          { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
        ]
      }
    })
    await wrapper.find('.list-item').trigger('click')
    expect(wrapper.emitted('stock-click')).toBeTruthy()
  })
})
```

---

## 4. E2E 測試

### 4.1 Playwright 測試

#### tests/e2e/homepage.spec.ts

```typescript
/**首頁 E2E 測試 */
import { test, expect } from '@playwright/test'

test.describe('首頁', () => {
  test('顯示行事曆模式', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.calendar')).toBeVisible()
  })
  
  test('切換至列表模式', async ({ page }) => {
    await page.goto('/')
    await page.click('text=列表')
    await expect(page.locator('.list-view')).toBeVisible()
  })
  
  test('切換回行事曆模式', async ({ page }) => {
    await page.goto('/')
    await page.click('text=列表')
    await page.click('text=行事曆')
    await expect(page.locator('.calendar')).toBeVisible()
  })
})

test.describe('搜尋', () => {
  test('搜尋股票代號', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', '2330')
    await expect(page.locator('.search-result')).toContainText('台積電')
  })
  
  test('點擊搜尋結果導航至歷史頁面', async ({ page }) => {
    await page.goto('/')
    await page.fill('input[placeholder*="搜尋"]', '2330')
    await page.click('.search-result')
    await expect(page).toHaveURL(/\/stock\/2330/)
  })
})

test.describe('單股歷史', () => {
  test('從列表點擊股票導航至歷史頁面', async ({ page }) => {
    await page.goto('/')
    await page.click('text=列表')
    await page.click('.list-item >> text=2330')
    await expect(page).toHaveURL(/\/stock\/2330/)
    await expect(page.locator('.stock-name')).toContainText('台積電')
  })
  
  test('返回按鈕回首頁', async ({ page }) => {
    await page.goto('/stock/2330')
    await page.click('text=返回')
    await expect(page).toHaveURL('/')
  })
})
```

---

## 5. 測試覆蓋矩陣

| BDD Scenario | 單元測試 | 整合測試 | E2E 測試 |
|--------------|:--------:|:--------:|:--------:|
| 開啟網站顯示行事曆 | - | Calendar | ✅ |
| 切換至列表模式 | - | - | ✅ |
| 切換回行事曆模式 | - | - | ✅ |
| 點擊日期查看配息股票 | useCalendar | Calendar | ✅ |
| 點擊無配息的日期 | useCalendar | Calendar | ⬜ |
| 從行事曆查看單股歷史 | - | StockDetail | ✅ |
| 從列表查看單股歷史 | - | ListView | ✅ |
| 返回首頁 | - | - | ✅ |
| 搜尋股票代號 | useSearch | SearchBar | ✅ |
| 搜尋股票名稱 | useSearch | SearchBar | ✅ |
| 點擊搜尋結果 | - | - | ✅ |
| 搜尋無結果 | useSearch | SearchBar | ✅ |
| 資料載入中 | - | LoadingState | ⬜ |
| 資料載入成功 | - | LoadingState | ⬜ |
| 資料載入失敗 | - | ErrorState | ✅ |
| 點擊重試按鈕 | - | ErrorState | ✅ |
| 無未來配息資料 | - | EmptyState | ⬜ |
| 手機版顯示 | - | - | ✅ |
| 深色模式切換 | - | - | ✅ |

**圖例**：✅ 已規劃 · ⬜ 未規劃 · - 不適用

---

## 6. 測試執行

### 6.1 Python 測試

```bash
# 執行所有 Python 測試
pytest crawler/ processor/ -v

# 執行特定測試
pytest crawler/test_integration.py -v

# 產生覆蓋率報告
pytest --cov=crawler --cov=processor --cov-report=html
```

### 6.2 Vue 測試

```bash
# 執行所有 Vitest 測試
cd frontend && npm run test:unit

# 執行特定測試
npm run test:unit -- --run src/components/test/Calendar.spec.ts

# 產生覆蓋率報告
npm run test:unit -- --coverage
```

### 6.3 E2E 測試

```bash
# 執行 Playwright 測試
cd frontend && npx playwright test

# 執行特定測試
npx playwright test tests/e2e/homepage.spec.ts

# 互動模式（除錯）
npx playwright test --debug
```

---

## 7. 測試資料

### 7.1 Mock 資料

```python
# tests/fixtures/stock_data.json
{
  "code": "2330",
  "name": "台積電",
  "market": "TWSE",
  "type": "common",
  "dividend_history": [
    {
      "year": 2026,
      "ex_date": "2026-07-25",
      "cash_dividend": 3.5
    }
  ]
}
```

### 7.2 API Mock

```typescript
// tests/mocks/api.ts
export const mockUpcoming = [
  { code: '2330', name: '台積電', type: 'stock', ex_date: '2026-07-25', dividend: 3.5 },
  { code: '0056', name: '元大高股息', type: 'etf', ex_date: '2026-07-20', dividend: 1.8 }
]

export const mockSecuritiesIndex = [
  { code: '2330', name: '台積電' },
  { code: '0050', name: '元大台灣50' },
  { code: '0056', name: '元大高股息' }
]
```

---

## 8. 驗收標準

| 標準 | 目標 |
|------|------|
| Python 單元測試覆蓋率 | > 80% |
| Vue 單元測試覆蓋率 | > 70% |
| E2E 測試通過率 | 100% |
| 所有 BDD Scenario 覆蓋 | 100% |
| 測試執行時間 | < 5 分鐘 |

---

## 📝 備註

- 測試應在 CI/CD 中自動執行
- E2E 測試可使用真實 TWSE API 或 Mock
- 測試資料應涵蓋正常流程和異常情況
