# 行事曆載入邏輯分析

## A) 首頁行事曆的載入流程

### 觸發時機

`HomeView.vue` 在 `onMounted` 中呼叫：

```ts
const { status, errorMessage, load, retry, allMonths, getByDate, sortedUpcoming } = useUpcoming()
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(allMonths) // ← 無 loadMonth

onMounted(() => {
  load() // ← 不傳參數
})
```

### 資料流向

```
HomeView.onMounted
  └─ load()（無參數）
       ├─ fetchIndex() → 取得 index.json 的全部月份 key（如 ["2025-01", ..., "2025-07"]）
       └─ Promise.allSettled(monthKeys.map(fetchMonth))
            └─ 全部月份並行 fetch → 合併進 allMonths
```

### 關鍵問題

1. **一次性全量載入**：`load()` 不帶參數時，會 fetch `index.json` 取得所有可用品月份，然後**全部並行 fetch**。假設有 18 個月的資料，就是 18 個 HTTP 請求同時發出。

2. **useCalendar 無懶載入**：`useCalendar(allMonths)` 沒有傳入第二個參數 `loadMonth`，因此 `useCalendar` 內部的 `watch(currentDate, ...)` 永遠不會執行（`if (loadMonth)` 判斷為 false）。

3. **切換月份時無法補載**：使用者切到其他月份時，如果該月資料不在 `allMonths` 中（理論上不會，因為全量載入了），行事曆格子會是空的。

4. **status 管理**：全量載入期間 `status` 維持 `'loading'`，首頁會一直顯示 loading 狀態直到全部月份 fetch 完成。

---

## B) 追蹤清單的懶載入流程

### 觸發時機

`WatchlistView.vue` 在 `onMounted` 中：

```ts
onMounted(() => {
  if (status.value === 'loading') {
    load([currentMonthKey()]) // ← 只載入當月
  }
})
```

### 資料流向

```
WatchlistView.onMounted
  └─ load([currentMonthKey()])  // 僅載入當月
       └─ fetchMonth("2025-07") → allMonths

useCalendar(filteredMonths, loadMonth)  // ← 傳入 loadMonth callback
  └─ watch(currentDate, ...)  // 切換月份時
       └─ 若 allMonths 未含該月 → loadMonth(key) → ensureMonth(key)
            └─ fetchMonth(key) → 合併進 allMonths
```

### ensureMonth 運作方式

```ts
async function ensureMonth(monthKey: string): Promise<UpcomingDividend[]> {
  // 1. 已載入：直接回傳（cache hit）
  if (allMonths.value.has(monthKey)) {
    return allMonths.value.get(monthKey) ?? []
  }
  // 2. 未載入：fetch 該月（cache miss）
  const data = await fetchMonth(monthKey)
  // 合併進 allMonths
  merged.set(monthKey, data)
  allMonths.value = merged
  return data
}
```

### 列表模式的額外載入

```ts
function handleViewChange(view: ViewMode) {
  if (view === 'list') {
    load(getFutureMonths(5)) // 當月 + 未來 4 個月，共 5 個月
  } else {
    // 行事曆模式：確保當月已載入
    if (!allMonths.value.has(key)) {
      load([key])
    }
  }
}
```

### 關鍵優勢

- **首屏快速**：只 fetch 1 個月份檔案，延遲極低
- **按需載入**：切換月份時才 fetch 該月資料，不預先浪費
- **全局 cache**：`allMonths` 是 module-level singleton，跨 View 共享，fetch 過的月份不會重複請求

---

## C) 差異分析

| 面向 | 首頁 (HomeView) | 追蹤清單 (WatchlistView) |
|------|----------------|------------------------|
| **初始載入** | `load()` 全量載入所有月份 | `load([currentMonthKey()])` 只載入當月 |
| **HTTP 請求數** | 1（index.json）+ N（月份數） | 1（當月） |
| **首屏延遲** | 高（等所有月份 fetch 完） | 低（1 個月份即可渲染） |
| **useCalendar loadMonth** | 未傳入（無懶載入） | 傳入 `loadMonth` callback |
| **切換月份** | 全量已載入，不需要補載 | 自動 `ensureMonth` 補載 |
| **列表模式** | 直接使用已全量載入的資料 | 觸發 `load(getFutureMonths(5))` 載入 5 個月 |
| **資料過濾** | 無過濾，顯示所有配息 | `filteredMonths` 只保留追蹤清單內的股票 |

### 核心差異

首頁採用**「先全量再顯示」**策略，追蹤清單採用**「先最小再按需」**策略。首頁的全量載入在月份資料量大時會造成不必要的等待和網路消耗。

---

## D) 建議修改方案

### 目標

讓首頁行事曆採用與追蹤清單相同的懶載入邏輯，僅初始載入當月，切換月份時按需 fetch。

### 修改方案

#### 1. 修改 `HomeView.vue` 的 `onMounted`

```diff
- const { monthLabel, days, prevMonth, nextMonth } = useCalendar(allMonths)
+ const { monthLabel, days, prevMonth, nextMonth } = useCalendar(allMonths, loadMonth)

  onMounted(() => {
-   load()
+   load([currentMonthKey()])  // 只載入當月
  })
```

#### 2. 新增 `loadMonth` callback

```ts
async function loadMonth(monthKey: string): Promise<void> {
  await ensureMonth(monthKey)
}
```

#### 3. 列表模式需額外載入

```ts
function handleViewChange(view: ViewMode) {
  currentView.value = view
  if (view === 'list') {
    // 列表模式需要未來配息資料，載入當月 + 未來 4 個月
    const now = new Date()
    const futureMonths: string[] = []
    for (let i = 0; i < 5; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() + i, 1)
      futureMonths.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
    }
    load(futureMonths)
  }
}
```

#### 4. status 狀態調整

由於只載入 1 個月份，`status` 會快速從 `'loading'` 變為 `'success'`，首屏體驗大幅提升。

### 完整修改後的 HomeView.vue script 區塊

```ts
const { status, errorMessage, load, retry, ensureMonth, allMonths, getByDate, sortedUpcoming } = useUpcoming()

function currentMonthKey(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

async function loadMonth(monthKey: string): Promise<void> {
  await ensureMonth(monthKey)
}

const { monthLabel, days, prevMonth, nextMonth } = useCalendar(allMonths, loadMonth)

onMounted(() => {
  load([currentMonthKey()])
})

function getFutureMonths(count: number): string[] {
  const months: string[] = []
  const now = new Date()
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}

function handleViewChange(view: ViewMode) {
  currentView.value = view
  if (view === 'list') {
    load(getFutureMonths(5))
  } else {
    const key = currentMonthKey()
    if (!allMonths.value.has(key)) {
      load([key])
    }
  }
}
```

### 注意事項

1. **upcoming computed 依賴全量資料**：`sortedUpcoming` 會遍歷 `allMonths` 計算未來配息列表。懶載入模式下，如果 `allMonths` 只有當月資料，列表模式會缺少其他月份的配息項目。這正是 `handleViewChange` 在切換到列表模式時需要 `load(getFutureMonths(5))` 的原因。

2. **dividendDates computed**：`useUpcoming` 裡的 `dividendDates` 會計算所有已載入月份的配息日期集合，用於行事曆的日期標記。懶載入模式下只會包含已載入月份的日期，但因為 `useCalendar` 的 `days` computed 只會顯示當月格子，所以不受影響。

3. **module-level singleton**：`allMonths` 是跨 View 共享的，從首頁切到追蹤清單時，已載入的月份資料會保留，不會重複 fetch。

---

## 附錄：相關型別

```ts
// types/stock.ts
interface UpcomingDividend {
  code: string          // 證券代號
  name: string          // 證券名稱
  type: string          // stock | etf | preferred | 息
  ex_date: string       // 除權息日 YYYY-MM-DD
  pay_date?: string     // 發放日
  dividend?: number     // 現金配息金額
  cash_dividend?: number
  stock_dividend?: number
}

interface CalendarDay {
  date: string            // YYYY-MM-DD
  isCurrentMonth: boolean
  isToday: boolean
  hasDividend: boolean
  dividends: UpcomingDividend[]
}

type ViewMode = 'calendar' | 'list'
type LoadingStatus = 'loading' | 'success' | 'error' | 'empty'
```
