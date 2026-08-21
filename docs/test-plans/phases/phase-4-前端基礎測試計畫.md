# 測試計畫：Phase 4 前端基礎（行事曆 + 列表）

## 📋 概述

| 項目 | 內容 |
|------|------|
| **階段** | Phase 4 — 前端基礎 |
| **測試類型** | 單元測試、元件測試 |
| **工具** | Vitest + Vue Test Utils |
| **BDD 對應** | 首頁顯示、行事曆、列表模式切換 |

---

## 1. 測試項目

### 1.1 Composable 單元測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| useCalendar | 產生正確的日期資料 | useCalendar.spec.ts |
| useCalendar.prevMonth | 切換到上個月 | useCalendar.spec.ts |
| useCalendar.nextMonth | 切換到下個月 | useCalendar.spec.ts |
| useUpcoming | 載入 upcoming.json | useUpcoming.spec.ts |
| useUpcoming.getByDate | 按日期篩選 | useUpcoming.spec.ts |

### 1.2 Component 整合測試

| 測試項目 | 預期結果 | 測試檔案 |
|----------|----------|----------|
| Calendar 渲染 | 顯示行事曆格子 | Calendar.spec.ts |
| Calendar 標示配息日 | 有配息的日期有標示 | Calendar.spec.ts |
| Calendar 點擊事件 | 點擊日期觸發事件 | Calendar.spec.ts |
| ListView 渲染 | 顯示列表 | ListView.spec.ts |
| ListView 排序 | 依日期排序 | ListView.spec.ts |
| ListView 點擊事件 | 點擊股票觸發事件 | ListView.spec.ts |
| ViewSwitcher 切換 | 切換行事曆/列表 | ViewSwitcher.spec.ts |
| LoadingState | 顯示 loading | LoadingState.spec.ts |
| ErrorState | 顯示錯誤訊息 | ErrorState.spec.ts |

---

## 2. 測試案例

### 2.1 Composable 單元測試

```typescript
// frontend/src/composables/test/useCalendar.spec.ts
import { describe, it, expect } from 'vitest'
import { useCalendar } from '../useCalendar'

describe('useCalendar', () => {
  it('should generate calendar days for current month', () => {
    const { days, currentMonth } = useCalendar()
    
    expect(days.value.length).toBeGreaterThan(0)
    expect(days.value.length).toBeLessThanOrEqual(42) // 最多 6 週
    expect(currentMonth.value).toBeDefined()
  })
  
  it('should have correct day structure', () => {
    const { days } = useCalendar()
    
    const firstDay = days.value[0]
    expect(firstDay).toHaveProperty('date')
    expect(firstDay).toHaveProperty('isCurrentMonth')
    expect(firstDay).toHaveProperty('isToday')
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
  
  it('should mark dates with dividends', () => {
    const upcoming = [
      { code: '2330', ex_date: '2026-07-25', dividend: 3.5 }
    ]
    const { days } = useCalendar(upcoming)
    
    const dividendDay = days.value.find(d => d.date === '2026-07-25')
    expect(dividendDay?.hasDividend).toBe(true)
  })
})

// frontend/src/composables/test/useUpcoming.spec.ts
import { describe, it, expect } from 'vitest'
import { useUpcoming } from '../useUpcoming'

describe('useUpcoming', () => {
  it('should load upcoming data', async () => {
    const { upcoming, loading } = useUpcoming()
    
    expect(loading.value).toBe(true)
    
    await waitForNextTick()
    
    expect(loading.value).toBe(false)
    expect(upcoming.value).toBeDefined()
  })
  
  it('should filter by date', async () => {
    const { upcoming, getByDate } = useUpcoming()
    
    await waitForNextTick()
    
    const result = getByDate('2026-07-25')
    expect(Array.isArray(result)).toBe(true)
  })
})
```

### 2.2 Component 整合測試

```typescript
// frontend/src/components/test/Calendar.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Calendar from '../Calendar.vue'

describe('Calendar', () => {
  const mockUpcoming = [
    { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 },
    { code: '0056', name: '元大高股息', ex_date: '2026-07-20', dividend: 1.8 }
  ]
  
  it('renders calendar grid', () => {
    const wrapper = mount(Calendar, {
      props: { upcoming: mockUpcoming }
    })
    
    expect(wrapper.find('.calendar-grid').exists()).toBe(true)
    expect(wrapper.find('.calendar-header').exists()).toBe(true)
  })
  
  it('displays current month', () => {
    const wrapper = mount(Calendar, {
      props: { upcoming: mockUpcoming }
    })
    
    const header = wrapper.find('.calendar-header').text()
    expect(header).toMatch(/\d{4} 年 \d{1,2} 月/)
  })
  
  it('highlights dates with dividends', () => {
    const wrapper = mount(Calendar, {
      props: { upcoming: mockUpcoming }
    })
    
    const dividendDay = wrapper.find('[data-date="2026-07-25"]')
    expect(dividendDay.classes()).toContain('has-dividend')
  })
  
  it('emits date-click when clicking date with dividend', async () => {
    const wrapper = mount(Calendar, {
      props: { upcoming: mockUpcoming }
    })
    
    await wrapper.find('[data-date="2026-07-25"]').trigger('click')
    
    expect(wrapper.emitted('date-click')).toBeTruthy()
    expect(wrapper.emitted('date-click')![0]).toEqual(['2026-07-25'])
  })
  
  it('emits month-change when navigating', async () => {
    const wrapper = mount(Calendar, {
      props: { upcoming: mockUpcoming }
    })
    
    await wrapper.find('.prev-month').trigger('click')
    
    expect(wrapper.emitted('month-change')).toBeTruthy()
  })
})

// frontend/src/components/test/ListView.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ListView from '../ListView.vue'

describe('ListView', () => {
  const mockUpcoming = [
    { code: '0056', name: '元大高股息', ex_date: '2026-07-20', dividend: 1.8 },
    { code: '2330', name: '台積電', ex_date: '2026-07-25', dividend: 3.5 }
  ]
  
  it('renders list items', () => {
    const wrapper = mount(ListView, {
      props: { upcoming: mockUpcoming }
    })
    
    const items = wrapper.findAll('.list-item')
    expect(items.length).toBe(2)
  })
  
  it('sorts by date ascending', () => {
    const wrapper = mount(ListView, {
      props: { upcoming: mockUpcoming }
    })
    
    const items = wrapper.findAll('.list-item')
    expect(items[0].text()).toContain('07-20')
    expect(items[1].text()).toContain('07-25')
  })
  
  it('displays stock info correctly', () => {
    const wrapper = mount(ListView, {
      props: { upcoming: mockUpcoming }
    })
    
    const firstItem = wrapper.find('.list-item')
    expect(firstItem.text()).toContain('0056')
    expect(firstItem.text()).toContain('元大高股息')
    expect(firstItem.text()).toContain('$1.80')
  })
  
  it('emits stock-click when clicking item', async () => {
    const wrapper = mount(ListView, {
      props: { upcoming: mockUpcoming }
    })
    
    await wrapper.find('.list-item').trigger('click')
    
    expect(wrapper.emitted('stock-click')).toBeTruthy()
  })
})

// frontend/src/components/test/ViewSwitcher.spec.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ViewSwitcher from '../ViewSwitcher.vue'

describe('ViewSwitcher', () => {
  it('renders calendar and list tabs', () => {
    const wrapper = mount(ViewSwitcher, {
      props: { currentView: 'calendar' }
    })
    
    expect(wrapper.find('[data-view="calendar"]').exists()).toBe(true)
    expect(wrapper.find('[data-view="list"]').exists()).toBe(true)
  })
  
  it('highlights current view', () => {
    const wrapper = mount(ViewSwitcher, {
      props: { currentView: 'calendar' }
    })
    
    expect(wrapper.find('[data-view="calendar"]').classes()).toContain('active')
  })
  
  it('emits view-change when clicking tab', async () => {
    const wrapper = mount(ViewSwitcher, {
      props: { currentView: 'calendar' }
    })
    
    await wrapper.find('[data-view="list"]').trigger('click')
    
    expect(wrapper.emitted('view-change')).toBeTruthy()
    expect(wrapper.emitted('view-change')![0]).toEqual(['list'])
  })
})
```

---

## 3. 測試執行

```bash
# 執行所有 Vitest 測試
cd frontend && npm run test:unit

# 執行特定測試
npm run test:unit -- --run src/components/test/Calendar.spec.ts

# 監聽模式
npm run test:unit -- --watch

# 產生覆蓋率報告
npm run test:unit -- --coverage
```

---

## 4. 驗收標準

| 標準 | 目標 |
|------|------|
| Composable 測試通過率 | 100% |
| Component 測試通過率 | 100% |
| 測試覆蓋率 | > 70% |
| 行事曆顯示 | 正確顯示當月 |
| 列表排序 | 依日期排序 |
| 模式切換 | 即時切換無延遲 |
| 載入狀態 | 正確顯示 loading |
| 錯誤狀態 | 正確顯示錯誤訊息 |

---

## 5. 測試資料

```typescript
// frontend/src/__mocks__/api.ts
export const mockUpcoming = [
  {
    code: '2330',
    name: '台積電',
    type: 'stock',
    ex_date: '2026-07-25',
    pay_date: '2026-08-15',
    dividend: 3.5
  },
  {
    code: '0056',
    name: '元大高股息',
    type: 'etf',
    ex_date: '2026-07-20',
    pay_date: '2026-08-10',
    dividend: 1.8
  }
]
```
