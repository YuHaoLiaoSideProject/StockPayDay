# Phase 4 前端基礎（行事曆 + 列表） — 開發規格

> **技術棧**：Vue 3.x (Composition API) · Vite 5.x · Tailwind CSS 3.x · Vitest · Vue Test Utils
> **操作流程**：`docs/interaction-flows/phases/phase-4-前端基礎.md`
> **BDD**：`docs/bdds/stockpayday.feature`
> **測試計畫**：`docs/test-plans/phases/phase-4-前端基礎測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

建立前端基礎框架，提供未來配息資料的行事曆與列表兩種瀏覽模式。核心包含：

1. **專案初始化**：Vite + Vue 3 + Tailwind CSS 骨架建立
2. **資料層**：`useUpcoming` composable — 靜態 fetch `api/upcoming.json`
3. **行事曆模式**：`Calendar.vue` — 月份導航、配息日標示、日期點擊
4. **列表模式**：`ListView.vue` — 依日期排序的配息列表
5. **模式切換**：`ViewSwitcher.vue` — 行事曆/列表 Tab 切換
6. **狀態管理**：Loading / Error / Empty 三態處理
7. **深色模式**：系統偏好偵測 + 手動切換 + localStorage 持久化
8. **響應式設計**：手機 / 平板 / 桌機佈局

---

## 1. 後端實作規格（不適用）

本階段為純前端，無後端改動。`api/upcoming.json` 由 Phase 3 processor 產出。

---

## 2. 前端實作規格

### 2.1 檔案改動總覽

```
frontend/
├── index.html                         ← 新增：HTML 入口
├── package.json                       ← 新增：依賴聲明
├── vite.config.ts                     ← 新增：Vite 配置
├── tailwind.config.js                 ← 新增：Tailwind 配置
├── postcss.config.js                  ← 新增：PostCSS 配置
├── tsconfig.json                      ← 新增：TypeScript 配置
├── src/
│   ├── main.ts                        ← 新增：Vue 應用入口
│   ├── App.vue                        ← 新增：根組件（Layout + Router）
│   ├── types/
│   │   └── stock.ts                   ← 新增：共用型別定義
│   ├── composables/
│   │   ├── useUpcoming.ts             ← 新增：配息資料載入
│   │   ├── useCalendar.ts             ← 新增：行事曆日期計算
│   │   └── useDarkMode.ts             ← 新增：深色模式管理
│   ├── components/
│   │   ├── Calendar.vue               ← 新增：行事曆組件
│   │   ├── CalendarDay.vue            ← 新增：單日格子組件
│   │   ├── ListView.vue               ← 新增：列表模式組件
│   │   ├── ListItem.vue               ← 新增：列表項目組件
│   │   ├── ViewSwitcher.vue           ← 新增：模式切換 Tab
│   │   ├── DayDetail.vue              ← 新增：日期配息明細 Modal
│   │   ├── LoadingState.vue           ← 新增：載入中畫面
│   │   ├── ErrorState.vue             ← 新增：錯誤畫面
│   │   └── EmptyState.vue             ← 新增：空狀態畫面
│   └── views/
│       └── HomeView.vue               ← 新增：首頁視圖
```

### 2.2 型別定義 — `types/stock.ts`

```typescript
/**
 * 配息資料（來自 api/upcoming.json）
 */
export interface UpcomingDividend {
  /** 證券代號，如 "2330" */
  code: string
  /** 證券名稱，如 "台積電" */
  name: string
  /** 證券類型：stock | etf | preferred */
  type: 'stock' | 'etf' | 'preferred'
  /** 除權息日，如 "2026-07-25" */
  ex_date: string
  /** 發放日，如 "2026-08-15" */
  pay_date: string
  /** 現金配息金額 */
  dividend: number
}

/**
 * 行事曆日期格子
 */
export interface CalendarDay {
  /** 日期字串 YYYY-MM-DD */
  date: string
  /** 是否屬於當前月份 */
  isCurrentMonth: boolean
  /** 是否為今天 */
  isToday: boolean
  /** 該日是否有配息 */
  hasDividend: boolean
  /** 該日配息資料（可能為空） */
  dividends: UpcomingDividend[]
}

/**
 * 顯示模式
 */
export type ViewMode = 'calendar' | 'list'

/**
 * 資料載入狀態
 */
export type LoadingStatus = 'loading' | 'success' | 'error' | 'empty'
```

### 2.3 `useUpcoming` composable

職責：從 `api/upcoming.json` 載入配息資料，提供查詢方法。

```typescript
// composables/useUpcoming.ts
import { ref, computed } from 'vue'
import type { UpcomingDividend, LoadingStatus } from '../types/stock'

/**
 * 配息資料管理 composable
 *
 * 載入 api/upcoming.json 並提供篩選功能。
 * 靜態站部署，fetch 相對路徑即可。
 */
export function useUpcoming() {
  const upcoming = ref<UpcomingDividend[]>([])
  const status = ref<LoadingStatus>('loading')
  const errorMessage = ref<string>('')

  /**
   * 載入 upcoming.json
   * 失敗時設定 status = 'error'
   */
  async function load(): Promise<void> {
    status.value = 'loading'
    errorMessage.value = ''

    try {
      const response = await fetch('api/upcoming.json')
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data: UpcomingDividend[] = await response.json()
      upcoming.value = data
      status.value = data.length === 0 ? 'empty' : 'success'
    } catch (e) {
      status.value = 'error'
      errorMessage.value = '資料載入失敗，請稍後再試'
    }
  }

  /**
   * 重新載入（重試）
   */
  async function retry(): Promise<void> {
    await load()
  }

  /**
   * 依日期取得配息資料
   * @param dateStr YYYY-MM-DD
   */
  function getByDate(dateStr: string): UpcomingDividend[] {
    return upcoming.value.filter(item => item.ex_date === dateStr)
  }

  /**
   * 依日期排序的配息列表（近的在前）
   */
  const sortedUpcoming = computed(() => {
    return [...upcoming.value].sort(
      (a, b) => a.ex_date.localeCompare(b.ex_date)
    )
  })

  /**
   * 所有有配息的日期集合（YYYY-MM-DD）
   */
  const dividendDates = computed(() => {
    return new Set(upcoming.value.map(item => item.ex_date))
  })

  return {
    upcoming,
    status,
    errorMessage,
    load,
    retry,
    getByDate,
    sortedUpcoming,
    dividendDates,
  }
}
```

### 2.4 `useCalendar` composable

職責：計算行事曆格子、月份導航、標記配息日。

```typescript
// composables/useCalendar.ts
import { ref, computed } from 'vue'
import type { CalendarDay, UpcomingDividend } from '../types/stock'

/**
 * 行事曆管理 composable
 *
 * 計算當月日曆格子（含前後月補齊），
 * 標記有配息的日期。
 */
export function useCalendar(dividendDates: Set<string>, upcoming: UpcomingDividend[]) {
  const currentDate = ref(new Date())

  /** 當前年月標題，如 "2026 年 7 月" */
  const monthLabel = computed(() => {
    const d = currentDate.value
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`
  })

  /**
   * 產生行事曆格子（最多 6 週 = 42 格）
   * - 第一格為當月 1 日前的補齊（isCurrentMonth = false）
   * - 最後一格為當月最後一日後的補齊
   */
  const days = computed<CalendarDay[]>(() => {
    const d = currentDate.value
    const year = d.getFullYear()
    const month = d.getMonth()

    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)

    // 1 日是星期幾（0=日, 6=六）
    const startWeekday = firstDay.getDay()
    // 當月總天數
    const totalDays = lastDay.getDate()

    const today = new Date()
    const todayStr = formatDate(today)

    const result: CalendarDay[] = []

    // 補齊前月
    for (let i = startWeekday - 1; i >= 0; i--) {
      const date = new Date(year, month, -i)
      result.push(createDay(date, todayStr, dividendDates, upcoming))
    }

    // 當月
    for (let d = 1; d <= totalDays; d++) {
      const date = new Date(year, month, d)
      result.push(createDay(date, todayStr, dividendDates, upcoming))
    }

    // 補齊後月（確保至少 35 格 = 5 週）
    while (result.length < 35) {
      const date = new Date(year, month, totalDays + result.length - startWeekday + 1)
      result.push(createDay(date, todayStr, dividendDates, upcoming))
    }

    return result
  })

  /** 切換到上個月 */
  function prevMonth(): void {
    const d = currentDate.value
    currentDate.value = new Date(d.getFullYear(), d.getMonth() - 1, 1)
  }

  /** 切換到下個月 */
  function nextMonth(): void {
    const d = currentDate.value
    currentDate.value = new Date(d.getFullYear(), d.getMonth() + 1, 1)
  }

  return { currentDate, monthLabel, days, prevMonth, nextMonth }
}

/** 格式化日期為 YYYY-MM-DD */
function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/** 建立單日格子 */
function createDay(
  date: Date,
  todayStr: string,
  dividendDates: Set<string>,
  upcoming: UpcomingDividend[]
): CalendarDay {
  const dateStr = formatDate(date)
  const now = new Date()
  const isCurrentMonth = date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear()

  return {
    date: dateStr,
    isCurrentMonth: date.getMonth() === now.getMonth(), // 相對於 currentDate
    isToday: dateStr === todayStr,
    hasDividend: dividendDates.has(dateStr),
    dividends: upcoming.filter(item => item.ex_date === dateStr),
  }
}
```

> **注意**：`isCurrentMonth` 的判斷需相對於 `currentDate` 而非 `new Date()`，實作時應將 `currentDate` 傳入。

### 2.5 `useDarkMode` composable

職責：深色模式偵測、切換、持久化。

```typescript
// composables/useDarkMode.ts
import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'stockpayday-dark-mode'

/**
 * 深色模式管理 composable
 *
 * 1. 優先讀取 localStorage
 * 2. 無設定時偵測系統偏好 (prefers-color-scheme)
 * 3. 切換時寫入 localStorage 並更新 <html> class
 */
export function useDarkMode() {
  const isDark = ref<boolean>(initDarkMode())

  watchEffect(() => {
    applyDarkMode(isDark.value)
  })

  /** 切換深色/淺色 */
  function toggle(): void {
    isDark.value = !isDark.value
    localStorage.setItem(STORAGE_KEY, String(isDark.value))
  }

  return { isDark, toggle }
}

function initDarkMode(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored !== null) return stored === 'true'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyDarkMode(dark: boolean): void {
  document.documentElement.classList.toggle('dark', dark)
}
```

### 2.6 `Calendar.vue` 組件

```vue
<script setup lang="ts">
/**
 * 行事曆組件
 *
 * Props:
 *   - monthLabel: 月份標題
 *   - days: 行事曆格子資料
 *
 * Emits:
 *   - date-click(date: string) — 點擊日期
 *   - prev-month — 切換上月
 *   - next-month — 切換下月
 */
defineProps<{
  monthLabel: string
  days: CalendarDay[]
}>()

const emit = defineEmits<{
  'date-click': [date: string]
  'prev-month': []
  'next-month': []
}>()

// 星期標題
const weekHeaders = ['日', '一', '二', '三', '四', '五', '六']
</script>

<template>
  <div class="calendar">
    <!-- 月份導航 -->
    <div class="calendar-header">
      <button class="prev-month" @click="emit('prev-month')">‹</button>
      <h2 class="month-label">{{ monthLabel }}</h2>
      <button class="next-month" @click="emit('next-month')">›</button>
    </div>

    <!-- 星期標題列 -->
    <div class="calendar-weekdays">
      <div v-for="day in weekHeaders" :key="day" class="weekday">{{ day }}</div>
    </div>

    <!-- 日期格子（7 欄） -->
    <div class="calendar-grid">
      <CalendarDay
        v-for="item in days"
        :key="item.date"
        :day="item"
        @click="emit('date-click', item.date)"
      />
    </div>
  </div>
</template>
```

### 2.7 `CalendarDay.vue` 組件

```vue
<script setup lang="ts">
/**
 * 單日格子
 *
 * 標示是否有配息（has-dividend class），
 * 非當月日期半透明。
 */
import type { CalendarDay } from '../types/stock'

defineProps<{ day: CalendarDay }>()
</script>

<template>
  <div
    class="calendar-day"
    :class="{
      'other-month': !day.isCurrentMonth,
      'is-today': day.isToday,
      'has-dividend': day.hasDividend,
    }"
    :data-date="day.date"
  >
    <span class="day-number">{{ new Date(day.date + 'T00:00:00').getDate() }}</span>
    <span v-if="day.hasDividend" class="dividend-dot"></span>
  </div>
</template>
```

### 2.8 `ListView.vue` 組件

```vue
<script setup lang="ts">
/**
 * 列表模式組件
 *
 * Props:
 *   - items: 已依日期排序的配息資料
 *
 * Emits:
 *   - stock-click(code: string) — 點擊股票（Phase 5 導航）
 */
import type { UpcomingDividend } from '../types/stock'

defineProps<{ items: UpcomingDividend[] }>()

defineEmits<{
  'stock-click': [code: string]
}>()
</script>

<template>
  <div class="list-view">
    <ListItem
      v-for="item in items"
      :key="`${item.code}-${item.ex_date}`"
      :dividend="item"
      @click="emit('stock-click', item.code)"
    />
    <EmptyState v-if="items.length === 0" message="目前沒有即將配息的證券" />
  </div>
</template>
```

### 2.9 `ListItem.vue` 組件

```vue
<script setup lang="ts">
/**
 * 列表項目
 *
 * 顯示：日期、代號、名稱、金額
 */
import type { UpcomingDividend } from '../types/stock'

defineProps<{ dividend: UpcomingDividend }>()
</script>

<template>
  <div class="list-item">
    <span class="item-date">{{ dividend.ex_date }}</span>
    <span class="item-code">{{ dividend.code }}</span>
    <span class="item-name">{{ dividend.name }}</span>
    <span class="item-amount">${{ dividend.dividend.toFixed(2) }}</span>
  </div>
</template>
```

### 2.10 `ViewSwitcher.vue` 組件

```vue
<script setup lang="ts">
/**
 * 模式切換 Tab
 *
 * Props:
 *   - currentView: 'calendar' | 'list'
 *
 * Emits:
 *   - view-change(view: ViewMode)
 */
import type { ViewMode } from '../types/stock'

defineProps<{ currentView: ViewMode }>()

const emit = defineEmits<{
  'view-change': [view: ViewMode]
}>()
</script>

<template>
  <div class="view-switcher">
    <button
      data-view="calendar"
      :class="{ active: currentView === 'calendar' }"
      @click="emit('view-change', 'calendar')"
    >
      📅 行事曆
    </button>
    <button
      data-view="list"
      :class="{ active: currentView === 'list' }"
      @click="emit('view-change', 'list')"
    >
      📋 列表
    </button>
  </div>
</template>
```

### 2.11 `DayDetail.vue` 組件

```vue
<script setup lang="ts">
/**
 * 日期配息明細 Modal
 *
 * 顯示某日所有配息股票，點擊可導航至單股歷史（Phase 5）。
 */
import type { UpcomingDividend } from '../types/stock'

defineProps<{
  date: string
  dividends: UpcomingDividend[]
}>()

const emit = defineEmits<{
  close: []
  'stock-click': [code: string]
}>()
</script>

<template>
  <div class="day-detail-overlay" @click.self="emit('close')">
    <div class="day-detail-modal">
      <div class="modal-header">
        <h3>{{ date }} 配息股票</h3>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>
      <div v-if="dividends.length === 0" class="empty-hint">
        該日無配息股票
      </div>
      <ul v-else class="dividend-list">
        <li
          v-for="item in dividends"
          :key="item.code"
          class="dividend-item"
          @click="emit('stock-click', item.code)"
        >
          <span class="code">{{ item.code }}</span>
          <span class="name">{{ item.name }}</span>
          <span class="amount">${{ item.dividend.toFixed(2) }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
```

### 2.12 狀態組件

```vue
<!-- LoadingState.vue -->
<script setup lang="ts">
/** 全頁載入中畫面 */
</script>
<template>
  <div class="loading-state">
    <div class="spinner"></div>
    <p>載入中...</p>
  </div>
</template>
```

```vue
<!-- ErrorState.vue -->
<script setup lang="ts">
/**
 * 錯誤畫面
 * Props: message (string)
 * Emits: retry
 */
defineProps<{ message: string }>()
defineEmits<{ retry: [] }>()
</script>
<template>
  <div class="error-state">
    <p class="error-message">{{ message }}</p>
    <button class="retry-btn" @click="emit('retry')">重試</button>
  </div>
</template>
```

```vue
<!-- EmptyState.vue -->
<script setup lang="ts">
/**
 * 空狀態畫面
 * Props: message (string)
 */
defineProps<{ message: string }>()
</script>
<template>
  <div class="empty-state">
    <p>{{ message }}</p>
  </div>
</template>
```

### 2.13 `HomeView.vue` 首頁視圖

```vue
<script setup lang="ts">
/**
 * 首頁視圖
 *
 * 職責：
 * 1. 管理顯示模式（calendar / list）
 * 2. 協調 useUpcoming + useCalendar
 * 3. 根據 status 顯示 Loading / Error / Empty / 內容
 * 4. 管理 DayDetail Modal 開關
 */
import { ref, onMounted } from 'vue'
import { useUpcoming } from '../composables/useUpcoming'
import { useCalendar } from '../composables/useCalendar'
import { useDarkMode } from '../composables/useDarkMode'
import type { ViewMode } from '../types/stock'

const { upcoming, status, errorMessage, load, retry, getByDate, sortedUpcoming, dividendDates } = useUpcoming()
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(dividendDates.value, upcoming.value)
const { isDark, toggle: toggleDark } = useDarkMode()

const currentView = ref<ViewMode>('calendar')
const selectedDate = ref<string | null>(null)

onMounted(() => {
  load()
})

function handleViewChange(view: ViewMode) {
  currentView.value = view
}

function handleDateClick(date: string) {
  selectedDate.value = date
}

function handleCloseDetail() {
  selectedDate.value = null
}

// 計算選中日期的配息資料
const selectedDividends = computed(() => {
  if (!selectedDate.value) return []
  return getByDate(selectedDate.value)
})
</script>

<template>
  <div class="home-view" :class="{ dark: isDark }">
    <!-- Header -->
    <header class="app-header">
      <h1>📅 StockPayDay++</h1>
      <button class="theme-toggle" @click="toggleDark">
        {{ isDark ? '☀️' : '🌙' }}
      </button>
    </header>

    <!-- 狀態處理 -->
    <LoadingState v-if="status === 'loading'" />
    <ErrorState v-else-if="status === 'error'" :message="errorMessage" @retry="retry" />
    <EmptyState v-else-if="status === 'empty'" message="目前沒有即將配息的證券" />

    <!-- 主要內容 -->
    <template v-else>
      <ViewSwitcher :current-view="currentView" @view-change="handleViewChange" />

      <Calendar
        v-if="currentView === 'calendar'"
        :month-label="monthLabel"
        :days="days"
        @prev-month="prevMonth"
        @next-month="nextMonth"
        @date-click="handleDateClick"
      />

      <ListView
        v-else
        :items="sortedUpcoming"
      />

      <!-- 日期明細 Modal -->
      <DayDetail
        v-if="selectedDate"
        :date="selectedDate"
        :dividends="selectedDividends"
        @close="handleCloseDetail"
      />
    </template>
  </div>
</template>
```

### 2.14 `App.vue` 根組件

```vue
<script setup lang="ts">
/**
 * 根組件
 *
 * 簡單路由：首頁 / 單股歷史（Phase 5）
 * Phase 4 僅實作首頁。
 */
import HomeView from './views/HomeView.vue'
</script>

<template>
  <HomeView />
</template>
```

### 2.15 專案初始化檔案

#### `package.json`

```json
{
  "name": "stockpayday-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "test:unit": "vitest run",
    "test:unit:watch": "vitest"
  },
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "@vue/test-utils": "^2.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0",
    "vitest": "^2.0.0",
    "vue-tsc": "^2.0.0"
  }
}
```

#### `vite.config.ts`

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  // 靜態站部署：base 設為相對路徑
  base: './',
  build: {
    outDir: '../api', // 輸出到 api/ 目錄供 GitHub Pages 部署
  },
  server: {
    proxy: {
      // 開發時 proxy api/ 到靜態 JSON
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      },
    },
  },
})
```

#### `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}
```

#### `index.html`

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>StockPayDay++ 股市配息行事曆</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

#### `src/main.ts`

```typescript
import { createApp } from 'vue'
import App from './App.vue'
import './style.css' // Tailwind 入口

createApp(App).mount('#app')
```

#### `src/style.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## 3. API 合約

本階段無後端 API，資料來自靜態 JSON 檔案。

| 方法 | 路徑 | 格式 | 說明 |
|------|------|------|------|
| GET | `api/upcoming.json` | JSON | 未來配息資料陣列 |

### `api/upcoming.json` 回應格式

```json
[
  {
    "code": "2330",
    "name": "台積電",
    "type": "stock",
    "ex_date": "2026-07-25",
    "pay_date": "2026-08-15",
    "dividend": 3.5
  }
]
```

> 由 Phase 3 processor 產出，前端僅讀取。

---

## 4. 資料流

```
┌─────────────────────────────────────────────────────┐
│  GitHub Pages (靜態託管)                              │
│  api/upcoming.json                                   │
└──────────────┬──────────────────────────────────────┘
               │ fetch (relative path)
               ▼
┌─────────────────────────────────────────────────────┐
│  useUpcoming composable                              │
│  ├─ load() → fetch('api/upcoming.json')              │
│  ├─ upcoming: Ref<UpcomingDividend[]>                │
│  ├─ status: Ref<LoadingStatus>                       │
│  ├─ sortedUpcoming (computed, 依 ex_date 排序)        │
│  ├─ dividendDates (computed, Set<string>)             │
│  └─ getByDate(date) → UpcomingDividend[]             │
└──────────────┬──────────────────────────────────────┘
               │ 作為 props 傳入
               ▼
┌─────────────────────────────────────────────────────┐
│  HomeView (協調者)                                    │
│  ├─ status → LoadingState / ErrorState / EmptyState  │
│  ├─ currentView → Calendar 或 ListView               │
│  └─ selectedDate → DayDetail Modal                   │
├─────────────────────────────────────────────────────┤
│  useCalendar (日期計算)                               │
│  ├─ days: ComputedRef<CalendarDay[]>                 │
│  ├─ monthLabel: ComputedRef<string>                  │
│  └─ prevMonth / nextMonth                            │
├─────────────────────────────────────────────────────┤
│  useDarkMode (主題管理)                               │
│  ├─ isDark: Ref<boolean>                             │
│  └─ toggle() → 更新 localStorage + <html> class      │
└─────────────────────────────────────────────────────┘
```

---

## 5. 生命週期

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 初始載入 | `onMounted` | 呼叫 `useUpcoming.load()` | fetch 完成（success / error / empty） |
| 顯示內容 | status = 'success' | 渲染 Calendar 或 ListView | 使用者切換模式或離開 |
| 顯示錯誤 | status = 'error' | 渲染 ErrorState | 使用者點擊重試 |
| 重試載入 | 使用者點擊「重試」 | 重新呼叫 `load()` | fetch 完成 |
| 日期選擇 | 使用者點擊日期 | 開啟 DayDetail Modal | 使用者關閉 Modal |
| 模式切換 | 使用者點擊 Tab | 更新 `currentView`，即時切換 | 使用者再次切換 |

---

## 6. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| 網路斷線無法載入資料 | BDD @edge-case | 顯示 ErrorState「資料載入失敗，請檢查網路後重試」+ 重試按鈕 |
| `api/upcoming.json` 404 | BDD Scenario | 顯示 ErrorState，status = 'error' |
| 無未來配息資料 | BDD Scenario | 顯示 EmptyState「目前沒有即將配息的證券」 |
| 點擊無配息的日期 | BDD Scenario | 開啟 DayDetail Modal，顯示「該日無配息股票」 |
| 深色模式 localStorage 讀取失敗 | Tech Decision | fallback 至系統偏好偵測 |
| `prefers-color-scheme` 不支援 | 響應式 | 預設淺色模式 |
| 資料格式異常（JSON parse 失敗） | 邊界情況 | catch error → status = 'error' |
| 行事曆跨月補齊格子 | 邊界情況 | 確保至少 5 週（35 格），後月日期 isCurrentMonth = false |

---

## 7. CSS 關鍵樣式

| class | 樣式重點 |
|-------|---------|
| `.calendar-grid` | CSS Grid 7 欄佈局，gap-1 |
| `.calendar-day` | aspect-square，flex 居中，cursor-pointer |
| `.calendar-day.other-month` | opacity-0.4，降低存在感 |
| `.calendar-day.is-today` | font-bold + ring border 高亮 |
| `.calendar-day.has-dividend` | bg-blue-50（淺色）/ bg-blue-900（深色），視覺標示 |
| `.dividend-dot` | w-1.5 h-1.5 rounded-full bg-blue-500，日期下方圓點 |
| `.list-item` | flex justify-between，py-3 border-b |
| `.list-item .item-amount` | font-semibold text-green-600（深色: text-green-400） |
| `.view-switcher` | flex gap-2，按鈕 active 狀態 bg-blue-500 text-white |
| `.day-detail-overlay` | fixed inset-0 bg-black/50 z-50，點擊外部關閉 |
| `.day-detail-modal` | bg-white rounded-lg p-6 max-w-sm mx-auto（深色: bg-gray-800） |
| `.loading-state` | flex flex-col items-center justify-center min-h-screen |
| `.spinner` | w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin |
| `.error-state` | text-center p-8，紅色圖示 + 錯誤訊息 + 重試按鈕 |
| `.empty-state` | text-center p-8 text-gray-500 |
| `.theme-toggle` | p-2 rounded-full hover:bg-gray-200（深色: hover:bg-gray-700） |

> CSS class 名稱須與前端 code skeleton 的 class binding 一致。Tailwind utility class 為主要樣式方案，上述為關鍵自定義 class。

---

## 8. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 建立 frontend/ 專案骨架（Vite + Vue 3 + Tailwind CSS + TypeScript） | - |
| 2 | 定義 `types/stock.ts` 共用型別 | #1 |
| 3 | 實作 `useUpcoming` composable | #2 |
| 4 | 實作 `useCalendar` composable | #2 |
| 5 | 實作 `useDarkMode` composable | #1 |
| 6 | 建立狀態組件（LoadingState / ErrorState / EmptyState） | #1 |
| 7 | 實作 `CalendarDay.vue` 單日格子 | #2 |
| 8 | 實作 `Calendar.vue` 行事曆組件 | #4, #7 |
| 9 | 實作 `ListItem.vue` 列表項目 | #2 |
| 10 | 實作 `ListView.vue` 列表組件 | #9 |
| 11 | 實作 `ViewSwitcher.vue` 模式切換 | #2 |
| 12 | 實作 `DayDetail.vue` 日期明細 Modal | #2 |
| 13 | 建立 `HomeView.vue` 首頁視圖（整合所有組件） | #3, #4, #5, #6, #8, #10, #11, #12 |
| 14 | 建立 `App.vue` + `main.ts` 入口 | #13 |
| 15 | 執行 `npm install` 驗證專案可啟動 | #1 |
| 16 | 撰寫單元測試（useUpcoming / useCalendar / useDarkMode） | #3, #4, #5 |
| 17 | 撰寫元件測試（Calendar / ListView / ViewSwitcher） | #8, #10, #11 |
| 18 | 手動驗證：行事曆顯示、模式切換、深色模式、RWD | #14 |

---

## 9. 基礎架構設定

### Vite 開發伺服器

```bash
cd frontend
npm install
npm run dev
# 開啟 http://localhost:5173
```

### GitHub Pages 部署

Vite build 輸出至 `../api/`，GitHub Actions workflow（Phase 3 已設定）會自動部署 `api/` 目錄至 GitHub Pages。

```typescript
// vite.config.ts
build: {
  outDir: '../api', // 輸出與 api/ 目錄合併
}
```

> ⚠️ 需注意：Vite build 輸出會覆蓋 api/ 目錄下的靜態 JSON。建議 build 輸出到 `dist/`，再由 GitHub Actions workflow 將 `dist/` 與 `api/` 合併後部署。或將 `api/upcoming.json` 放入 `frontend/public/api/` 作為靜態資源複製。

### 環境變數

本階段無需額外環境變數。靜態 JSON 透過相對路徑 fetch。

---

## BDD Scenario 追溯對照表

| BDD Scenario | 對應組件/Composable | 對應規格章節 |
|---|---|---|
| 開啟網站顯示行事曆模式 | HomeView + Calendar | §2.13, §2.6 |
| 切換至列表模式 | ViewSwitcher + ListView | §2.10, §2.8 |
| 切換回行事曆模式 | ViewSwitcher + Calendar | §2.10, §2.6 |
| 點擊日期查看配息股票 | Calendar → DayDetail | §2.6, §2.12 |
| 點擊無配息的日期 | DayDetail（空列表） | §2.12 |
| 資料載入中 | LoadingState | §2.12 |
| 資料載入成功 | useUpcoming status → HomeView | §2.3, §2.13 |
| 資料載入失敗 | ErrorState + useUpcoming | §2.3, §2.12 |
| 點擊重試按鈕 | ErrorState → useUpcoming.retry | §2.3, §2.12 |
| 無未來配息資料 | EmptyState | §2.12 |
| 顯示個股/ETF/特別股配息 | useUpcoming（統一處理） | §2.3 |
| 手機版顯示 | Tailwind RWD classes | §7 |
| 平板版顯示 | Tailwind RWD classes | §7 |
| 桌機版顯示 | Tailwind RWD classes | §7 |
| 偵測系統深色模式偏好 | useDarkMode initDarkMode | §2.5 |
| 偵測系統淺色模式偏好 | useDarkMode initDarkMode | §2.5 |
| 手動切換深色模式 | useDarkMode.toggle | §2.5 |
| 手動切換淺色模式 | useDarkMode.toggle | §2.5 |
| 網路斷線時顯示錯誤 | useUpcoming + ErrorState | §2.3, §6 |
| 搜尋欄為空時（不顯示下拉） | Phase 5，本規格不涵蓋 | — |
