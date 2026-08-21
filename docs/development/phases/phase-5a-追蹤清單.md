# Phase 5a 追蹤清單 — 開發規格

> **技術棧**：Vue 3.x (Composition API) · Vite 5.x · Tailwind CSS 3.x · Vitest · Vue Test Utils
> **Tech Decision**：`docs/tech-decision-stockpayday-2026-07-21.md`
> **前置階段**：Phase 4（前端基礎）、Phase 5（前端進階）
> **狀態**：設計完成，待開發

---

## 概述

建立追蹤清單功能，讓使用者可收藏感兴趣的證券，並在專屬頁面查看其行事曆/列表。核心包含：

1. **useWatchlist composable**：追蹤清單管理（CRUD + localStorage 持久化）
2. **WatchlistButton 元件**：加入/移除追蹤按鈕（❤️ 圖示）
3. **WatchlistView 元件**：追蹤股票的行事曆/列表顯示
4. **Watchlist 頁面**：追蹤清單專屬路由（`/watchlist`）
5. **整合现有元件**：在 StockDetail、ListItem、CalendarDay 加入追蹤按鈕
6. **導覽列整合**：新增追蹤清單 Tab/連結

---

## 1. 前端實作規格

### 1.1 檔案改動總覽

```
frontend/src/
├── composables/
│   └── useWatchlist.ts              ← 新增：追蹤清單管理
├── components/
│   ├── WatchlistButton.vue          ← 新增：加入/移除追蹤按鈕
│   ├── WatchlistView.vue            ← 新增：追蹤清單行事曆/列表視圖
│   └── WatchlistEmpty.vue           ← 新增：追蹤清單空狀態
├── views/
│   └── Watchlist.vue                ← 新增：追蹤清單頁面
├── router/
│   └── index.ts                     ← 修改：新增 /watchlist 路由
├── App.vue                          ← 修改：導覽列加入追蹤清單連結
├── views/
│   └── Stock.vue                    ← 修改：加入 WatchlistButton
└── components/
    ├── ListItem.vue                 ← 修改：加入 WatchlistButton
    └── CalendarDay.vue              ← 修改：顯示追蹤標記
```

### 1.2 型別定義 — `types/watchlist.ts`

```typescript
/**
 * 追蹤清單相關型別
 */

/** 追蹤項目 */
export interface WatchlistItem {
  /** 證券代號，如 "2330" */
  code: string
  /** 證券名稱，如 "台積電" */
  name: string
  /** 證券類型：stock | etf | preferred */
  type: 'stock' | 'etf' | 'preferred'
  /** 加入追蹤的時間戳記 */
  addedAt: number
}

/** 追蹤清單排序方式 */
export type WatchlistSortBy = 'addedAt' | 'code' | 'name' | 'nextDividend'

/** 追蹤清單顯示模式 */
export type WatchlistViewMode = 'calendar' | 'list'
```

### 1.3 `useWatchlist` composable

職責：管理追蹤清單，提供新增/移除/查詢功能，資料持久化至 localStorage。

```typescript
// composables/useWatchlist.ts
import { ref, computed, watchEffect } from 'vue'
import type { WatchlistItem, WatchlistSortBy } from '../types/watchlist'
import type { UpcomingDividend } from '../types/stock'

const STORAGE_KEY = 'stockpayday-watchlist'

/**
 * 追蹤清單管理 composable
 *
 * 功能：
 * - 新增/移除追蹤股票
 * - 查詢是否已追蹤
 * - 取得追蹤清單（可排序）
 * - 與 upcoming 資料合併，顯示追蹤股票的配息資訊
 * - localStorage 持久化
 */
export function useWatchlist() {
  const items = ref<WatchlistItem[]>([])
  const sortBy = ref<WatchlistSortBy>('addedAt')

  // 初始化：從 localStorage 讀取
  function init(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          items.value = parsed
        }
      }
    } catch {
      // localStorage 讀取失敗，使用空列表
      items.value = []
    }
  }

  // 監聽變化，自動儲存
  watchEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value))
    } catch {
      // localStorage 寫入失敗（可能已滿）
    }
  })

  /**
   * 新增追蹤
   * @param code 證券代號
   * @param name 證券名稱
   * @param type 證券類型
   */
  function add(code: string, name: string, type: WatchlistItem['type'] = 'stock'): void {
    if (isWatched(code)) return

    items.value.push({
      code,
      name,
      type,
      addedAt: Date.now(),
    })
  }

  /**
   * 移除追蹤
   * @param code 證券代號
   */
  function remove(code: string): void {
    items.value = items.value.filter(item => item.code !== code)
  }

  /**
   * 切換追蹤狀態（加入/移除）
   * @param code 證券代號
   * @param name 證券名稱（新增時需要）
   * @param type 證券類型（新增時需要）
   */
  function toggle(code: string, name: string, type: WatchlistItem['type'] = 'stock'): void {
    if (isWatched(code)) {
      remove(code)
    } else {
      add(code, name, type)
    }
  }

  /**
   * 查詢是否已追蹤
   * @param code 證券代號
   */
  function isWatched(code: string): boolean {
    return items.value.some(item => item.code === code)
  }

  /**
   * 取得追蹤的證券代號列表
   */
  const watchedCodes = computed(() => {
    return new Set(items.value.map(item => item.code))
  })

  /**
   * 排序後的追蹤清單
   */
  const sortedItems = computed(() => {
    const sorted = [...items.value]

    switch (sortBy.value) {
      case 'addedAt':
        // 最新的在前
        return sorted.sort((a, b) => b.addedAt - a.addedAt)
      case 'code':
        return sorted.sort((a, b) => a.code.localeCompare(b.code))
      case 'name':
        return sorted.sort((a, b) => a.name.localeCompare(b.name, 'zh-TW'))
      case 'nextDividend':
        // 由外部合併 upcoming 資料後排序
        return sorted
      default:
        return sorted
    }
  })

  /**
   * 取得追蹤股票的配息資料
   * @param upcoming 所有即將配息的資料
   */
  function getWatchlistUpcoming(upcoming: UpcomingDividend[]): UpcomingDividend[] {
    return upcoming.filter(item => watchedCodes.value.has(item.code))
  }

  /**
   * 取得追蹤股票的配息日期集合
   * @param upcoming 所有即將配息的資料
   */
  function getWatchlistDividendDates(upcoming: UpcomingDividend[]): Set<string> {
    const watchlistUpcoming = getWatchlistUpcoming(upcoming)
    return new Set(watchlistUpcoming.map(item => item.ex_date))
  }

  /**
   * 清空追蹤清單
   */
  function clear(): void {
    items.value = []
  }

  // 初始化
  init()

  return {
    items,
    sortBy,
    sortedItems,
    watchedCodes,
    add,
    remove,
    toggle,
    isWatched,
    getWatchlistUpcoming,
    getWatchlistDividendDates,
    clear,
  }
}
```

### 1.4 `WatchlistButton.vue` 元件

加入/移除追蹤按鈕，顯示 ❤️ / 🤍 圖示。

```vue
<!-- components/WatchlistButton.vue -->

<script setup lang="ts">
/**
 * WatchlistButton 追蹤按鈕
 *
 * Props:
 *   - code: 證券代號
 *   - name: 證券名稱
 *   - type: 證券類型（預設 'stock'）
 *   - size: 按鈕大小（'sm' | 'md' | 'lg'，預設 'md'）
 *
 * Emits:
 *   - toggle(code: string, isWatched: boolean)
 */
import { computed } from 'vue'
import { useWatchlist } from '../composables/useWatchlist'

interface Props {
  code: string
  name: string
  type?: 'stock' | 'etf' | 'preferred'
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'stock',
  size: 'md',
})

const emit = defineEmits<{
  toggle: [code: string, isWatched: boolean]
}>()

const { isWatched, toggle: toggleWatchlist } = useWatchlist()

const watched = computed(() => isWatched(props.code))

function handleClick() {
  toggleWatchlist(props.code, props.name, props.type)
  emit('toggle', props.code, !watched.value)
}

// 尺寸 class
const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm': return 'w-6 h-6 text-sm'
    case 'lg': return 'w-10 h-10 text-xl'
    default: return 'w-8 h-8 text-base'
  }
})
</script>

<template>
  <button
    :class="[
      sizeClass,
      'flex items-center justify-center rounded-full transition-all duration-200',
      'hover:bg-surface-hover focus:outline-none focus:ring-2 focus:ring-accent',
      watched ? 'text-red-500' : 'text-text-muted hover:text-red-400'
    ]"
    :aria-label="watched ? '移除追蹤' : '加入追蹤'"
    :title="watched ? '移除追蹤' : '加入追蹤'"
    @click.stop="handleClick"
  >
    <!-- 已追蹤：實心愛心 -->
    <svg v-if="watched" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
      <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
    </svg>
    <!-- 未追蹤：空心愛心 -->
    <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
    </svg>
  </button>
</template>
```

### 1.5 `WatchlistView.vue` 元件

追蹤清單的行事曆/列表視圖，整合 useCalendar 顯示追蹤股票的配息日期。

```vue
<!-- components/WatchlistView.vue -->

<script setup lang="ts">
/**
 * WatchlistView 追蹤清單視圖
 *
 * 顯示追蹤股票的行事曆/列表模式。
 * 從 useWatchlist 取得追蹤清單，結合 upcoming 資料顯示配息資訊。
 */
import { ref, computed, watchEffect } from 'vue'
import { useWatchlist } from '../composables/useWatchlist'
import { useUpcoming } from '../composables/useUpcoming'
import { useCalendar } from '../composables/useCalendar'
import Calendar from './Calendar.vue'
import ListView from './ListView.vue'
import WatchlistEmpty from './WatchlistEmpty.vue'
import type { ViewMode, UpcomingDividend } from '../types/stock'

const { items, watchedCodes, getWatchlistUpcoming, getWatchlistDividendDates } = useWatchlist()
const { upcoming, status } = useUpcoming()

const currentView = ref<ViewMode>('calendar')

// 追蹤股票的配息資料
const watchlistUpcoming = computed(() => {
  return getWatchlistUpcoming(upcoming.value)
})

// 追蹤股票的配息日期
const watchlistDividendDates = computed(() => {
  return getWatchlistDividendDates(upcoming.value)
})

// 行事曆資料
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(
  watchlistDividendDates.value,
  watchlistUpcoming.value
)

// 依日期排序的列表
const sortedUpcoming = computed(() => {
  return [...watchlistUpcoming.value].sort(
    (a, b) => a.ex_date.localeCompare(b.ex_date)
  )
})

// 追蹤清單是否為空
const isEmpty = computed(() => items.value.length === 0)
</script>

<template>
  <div class="watchlist-view">
    <!-- 追蹤清單為空 -->
    <WatchlistEmpty v-if="isEmpty" />

    <!-- 有追蹤股票 -->
    <template v-else>
      <!-- 視圖切換 -->
      <div class="flex gap-2 mb-4">
        <button
          :class="[
            'px-4 py-2 rounded-lg transition-colors',
            currentView === 'calendar'
              ? 'bg-accent text-white'
              : 'bg-surface-secondary text-text-secondary hover:bg-surface-hover'
          ]"
          @click="currentView = 'calendar'"
        >
          📅 行事曆
        </button>
        <button
          :class="[
            'px-4 py-2 rounded-lg transition-colors',
            currentView === 'list'
              ? 'bg-accent text-white'
              : 'bg-surface-secondary text-text-secondary hover:bg-surface-hover'
          ]"
          @click="currentView = 'list'"
        >
          📋 列表
        </button>
      </div>

      <!-- 行事曆模式 -->
      <Calendar
        v-if="currentView === 'calendar'"
        :month-label="monthLabel"
        :days="days"
        @prev-month="prevMonth"
        @next-month="nextMonth"
      />

      <!-- 列表模式 -->
      <ListView
        v-else
        :items="sortedUpcoming"
      />

      <!-- 追蹤股票數量提示 -->
      <div class="mt-4 text-sm text-text-muted text-center">
        已追蹤 {{ items.length }} 支證券
      </div>
    </template>
  </div>
</template>
```

### 1.6 `WatchlistEmpty.vue` 元件

追蹤清單空狀態提示。

```vue
<!-- components/WatchlistEmpty.vue -->

<script setup lang="ts">
/**
 * WatchlistEmpty 追蹤清單空狀態
 *
 * 當使用者尚未加入任何追蹤時顯示。
 * 提供引導至搜尋或首頁的連結。
 */
import { useRouter } from 'vue-router'

const router = useRouter()

function goToSearch() {
  // 聚焦搜尋欄（由 App.vue 處理）
  document.querySelector<HTMLInputElement>('[data-search-input]')?.focus()
}

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="watchlist-empty flex flex-col items-center justify-center py-16 text-center">
    <!-- 圖示 -->
    <div class="text-6xl mb-4">📋</div>

    <!-- 標題 -->
    <h2 class="text-xl font-semibold text-text mb-2">
      追蹤清單是空的
    </h2>

    <!-- 說明 -->
    <p class="text-text-secondary mb-6 max-w-sm">
      在股票詳情頁或搜尋結果中點擊 ❤️ 按鈕，將感興趣的證券加入追蹤清單。
    </p>

    <!-- 操作按鈕 -->
    <div class="flex gap-3">
      <button
        class="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent-hover transition-colors"
        @click="goToSearch"
      >
        🔍 搜尋股票
      </button>
      <button
        class="px-4 py-2 bg-surface-secondary text-text-secondary rounded-lg hover:bg-surface-hover transition-colors"
        @click="goHome"
      >
        📅 查看行事曆
      </button>
    </div>
  </div>
</template>
```

### 1.7 `Watchlist.vue` 頁面

追蹤清單專屬路由頁面。

```vue
<!-- views/Watchlist.vue -->

<script setup lang="ts">
/**
 * Watchlist 追蹤清單頁面
 *
 * 路由：/watchlist
 * 功能：顯示追蹤股票的行事曆/列表視圖
 */
import WatchlistView from '../components/WatchlistView.vue'
</script>

<template>
  <div class="watchlist-page">
    <!-- 頁面標題 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-text">❤️ 我的追蹤清單</h1>
      <p class="text-text-secondary mt-1">追蹤感興趣的證券，掌握配息時程</p>
    </div>

    <!-- 追蹤清單視圖 -->
    <WatchlistView />
  </div>
</template>
```

### 1.8 Router 設定修改

新增 `/watchlist` 路由。

```typescript
// router/index.ts（修改摘要）

import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Stock from '@/views/Stock.vue'
import Watchlist from '@/views/Watchlist.vue'  // ← 新增

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/stock/:code',
      name: 'stock',
      component: Stock,
    },
    {
      path: '/watchlist',           // ← 新增
      name: 'watchlist',
      component: Watchlist,
    },
  ],
})

export default router
```

### 1.9 App.vue 導覽列修改

新增追蹤清單導覽連結。

```vue
<!-- App.vue（修改摘要） -->

<script setup lang="ts">
import { useRouter } from 'vue-router'
import SearchBar from '@/components/SearchBar.vue'
import { useWatchlist } from '@/composables/useWatchlist'

const router = useRouter()
const { items } = useWatchlist()

function goToWatchlist() {
  router.push('/watchlist')
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="p-4 border-b dark:border-gray-700">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <!-- Logo + 標題 -->
        <div class="flex items-center gap-4">
          <h1 class="text-xl font-bold">📅 StockPayDay++</h1>

          <!-- 追蹤清單按鈕 -->
          <button
            class="flex items-center gap-1 px-3 py-1.5 rounded-lg
                   bg-surface-secondary hover:bg-surface-hover
                   text-text-secondary transition-colors"
            @click="goToWatchlist"
          >
            <span>❤️</span>
            <span>追蹤清單</span>
            <!-- 追蹤數量徽章 -->
            <span
              v-if="items.length > 0"
              class="ml-1 px-1.5 py-0.5 text-xs bg-accent text-white rounded-full"
            >
              {{ items.length }}
            </span>
          </button>
        </div>

        <!-- 搜尋欄 -->
        <div class="w-64">
          <SearchBar />
        </div>
      </div>
    </header>

    <!-- Router View -->
    <main class="max-w-4xl mx-auto p-4">
      <router-view />
    </main>
  </div>
</template>
```

### 1.10 Stock.vue 頁面整合

在單股歷史頁面加入追蹤按鈕。

```vue
<!-- views/Stock.vue（修改摘要） -->

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStock } from '@/composables/useStock'
import StockDetail from '@/components/StockDetail.vue'
import WatchlistButton from '@/components/WatchlistButton.vue'

const route = useRoute()
const router = useRouter()

const code = computed(() => route.params.code as string)
const { stock, loading, error } = useStock(code)

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="stock-view max-w-2xl mx-auto p-4">
    <!-- StockDetail 加入追蹤按鈕 -->
    <div class="flex items-center justify-between mb-4">
      <button @click="goBack" class="text-blue-500 hover:underline">
        ← 返回
      </button>

      <!-- 追蹤按鈕（載入完成後顯示） -->
      <WatchlistButton
        v-if="stock"
        :code="stock.code"
        :name="stock.name"
        size="lg"
      />
    </div>

    <StockDetail
      :stock="stock"
      :loading="loading"
      :error="error"
      @back-click="goBack"
    />
  </div>
</template>
```

### 1.11 ListItem.vue 整合

在列表項目加入追蹤按鈕。

```vue
<!-- components/ListItem.vue（修改摘要） -->

<script setup lang="ts">
import type { UpcomingDividend } from '../types/stock'
import WatchlistButton from './WatchlistButton.vue'

defineProps<{ dividend: UpcomingDividend }>()

defineEmits<{
  'stock-click': [code: string]
}>()
</script>

<template>
  <div
    class="list-item flex items-center justify-between px-4 py-3
           border-b border-border hover:bg-surface-hover cursor-pointer"
    @click="emit('stock-click', dividend.code)"
  >
    <div class="flex items-center gap-3">
      <span class="text-text-secondary text-sm">{{ dividend.ex_date }}</span>
      <span class="font-medium text-text">{{ dividend.code }}</span>
      <span class="text-text-secondary">{{ dividend.name }}</span>
    </div>

    <div class="flex items-center gap-2">
      <span class="font-semibold text-accent">${{ dividend.dividend.toFixed(2) }}</span>

      <!-- 追蹤按鈕 -->
      <WatchlistButton
        :code="dividend.code"
        :name="dividend.name"
        :type="dividend.type"
        size="sm"
      />
    </div>
  </div>
</template>
```

### 1.12 CalendarDay.vue 整合

在行事曆日期格子顯示股票代號，追蹤優先，最多顯示 3 支。

```vue
<!-- components/CalendarDay.vue -->

<script setup lang="ts">
import { computed } from 'vue'
import type { CalendarDay } from '../types/stock'
import { useWatchlist } from '../composables/useWatchlist'

const props = defineProps<{ day: CalendarDay }>()

const { watchedCodes } = useWatchlist()
const MAX_DISPLAY = 3

// 該日是否有追蹤股票的配息
const hasWatchedDividend = computed(() => {
  return props.day.dividends.some(d => watchedCodes.value.has(d.code))
})

// 排序後的配息資料：追蹤優先，再依代號排序
const sortedDividends = computed(() => {
  return [...props.day.dividends].sort((a, b) => {
    const aWatched = watchedCodes.value.has(a.code) ? 0 : 1
    const bWatched = watchedCodes.value.has(b.code) ? 0 : 1
    if (aWatched !== bWatched) return aWatched - bWatched
    return a.code.localeCompare(b.code)
  })
})

// 顯示的配息項目（最多 3 支）
const displayedDividends = computed(() => {
  return sortedDividends.value.slice(0, MAX_DISPLAY)
})

// 超過 3 支的數量
const overflowCount = computed(() => {
  return Math.max(0, props.day.dividends.length - MAX_DISPLAY)
})

// 判斷是否為追蹤股票
function isWatched(code: string): boolean {
  return watchedCodes.value.has(code)
}
</script>

<template>
  <div
    class="calendar-day"
    :class="{
      'other-month': !day.isCurrentMonth,
      'is-today': day.isToday,
      'has-dividend': day.hasDividend,
      'has-watched': hasWatchedDividend,
    }"
    :data-date="day.date"
  >
    <span class="day-number">{{ new Date(day.date + 'T00:00:00').getDate() }}</span>
    
    <!-- 配息股票代號列表 -->
    <div v-if="day.hasDividend" class="dividend-labels">
      <span
        v-for="item in displayedDividends"
        :key="item.code"
        class="dividend-label"
        :class="{ 'dividend-label--watched': isWatched(item.code) }"
      >
        {{ item.code }}<span v-if="isWatched(item.code)" class="watched-heart">♥</span>
      </span>
      <span v-if="overflowCount > 0" class="dividend-more">
        +{{ overflowCount }}
      </span>
    </div>
  </div>
</template>
```

---

## 2. API 合約

本階段無新增後端 API。追蹤清單資料儲存於瀏覽器 localStorage。

### 2.1 localStorage 格式

| Key | 值類型 | 說明 |
|-----|--------|------|
| `stockpayday-watchlist` | JSON 陣列 | 追蹤清單陣列 |

#### `stockpayday-watchlist` 格式

```json
[
  {
    "code": "2330",
    "name": "台積電",
    "type": "stock",
    "addedAt": 1721616000000
  },
  {
    "code": "0056",
    "name": "元大高股息",
    "type": "etf",
    "addedAt": 1721616100000
  }
]
```

---

## 3. 資料流

```
[使用者點擊 ❤️ 按鈕]
       │
       ▼
[WatchlistButton]
  └─→ useWatchlist.toggle(code, name, type)
         │
         ├─→ add(code, name, type) ─┐
         │                          │
         └─→ remove(code) ──────────┤
                                    │
                                    ▼
                          [items.value 更新]
                                    │
                                    ▼
                          [watchEffect 觸發]
                                    │
                                    ▼
                          [localStorage 寫入]
                                    │
                                    ▼
                          [watchedCodes computed 更新]
                                    │
                   ┌────────────────┴────────────────┐
                   ▼                                  ▼
        [CalendarDay]                        [WatchlistView]
  顯示股票代號列表                      顯示追蹤股票配息
  追蹤優先 + ♥ 標記                     行事曆/列表模式
```

---

## 4. 生命週期

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 初始化 | `useWatchlist()` 呼叫 | 從 localStorage 讀取追蹤清單 | items.value 設定完成 |
| 加入追蹤 | 使用者點擊 ❤️ | toggle() → add() → items 更新 → watchEffect 儲存 | localStorage 已更新 |
| 移除追蹤 | 使用者點擊 ❤️ | toggle() → remove() → items 更新 → watchEffect 儲存 | localStorage 已更新 |
| 頁面載入 | `/watchlist` 路由載入 | WatchlistView 初始化，讀取追蹤清單 + upcoming | 資料載入完成 |
| 檢視追蹤 | 使用者瀏覽追蹤清單 | 顯示 sortedItems，可切換行事曆/列表 | 使用者離開頁面 |

---

## 5. 邊界條件處理

| 情境 | 處理方式 |
|------|---------|
| localStorage 不可用（隱私模式） | catch 儲存失敗，追蹤清單僅在當次 session 有效 |
| localStorage 已滿 | catch 寫入失敗，不影響其他功能 |
| 追蹤股票已下市 | 保留在追蹤清單中，顯示「無配息資料」提示 |
| 追蹤股票名稱變更 | 以 code 為主鍵，名稱不影響追蹤狀態 |
| 多裝置同步 | 不支援（靜態站 + localStorage），每台裝置獨立 |
| 追蹤清單為空 | 顯示 WatchlistEmpty 元件，引導使用者操作 |
| 即將配息資料為空 | 追蹤清單仍顯示，但行事曆/列表無配息標記 |
| 重複加入同一支股票 | isWatched() 檢查，不允許重複 |

---

## 6. CSS 關鍵樣式

| class / selector | 樣式重點 |
|-----------------|---------|
| `.watchlist-page` | 最大寬度 `max-w-4xl mx-auto` |
| `.watchlist-view` | 追蹤清單主容器 |
| `.watchlist-empty` | Flex 居中佈局，引導文字 + 按鈕 |
| `[data-watchlist-btn]` | 追蹤按鈕，hover 效果 |
| `.text-red-500` | 已追蹤狀態（實心愛心） |
| `.text-text-muted` | 未追蹤狀態（空心愛心） |
| `.watched-dot` | 追蹤標記圓點：`w-2 h-2 bg-red-500 rounded-full` |
| `.has-watched` | 行事曆格子有追蹤股票配息時的背景標記 |
| 徽章計數 | `px-1.5 py-0.5 text-xs bg-accent text-white rounded-full` |

---

## 7. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 建立 `types/watchlist.ts` 型別定義 | - |
| 2 | 實作 `useWatchlist` composable | #1 |
| 3 | 實作 `WatchlistButton` 元件 | #2 |
| 4 | 實作 `WatchlistEmpty` 元件 | - |
| 5 | 實作 `WatchlistView` 元件 | #2, #4 |
| 6 | 實作 `Watchlist` 頁面 | #5 |
| 7 | 修改 `router/index.ts` 新增路由 | #6 |
| 8 | 修改 `App.vue` 導覽列加入追蹤清單連結 | #2 |
| 9 | 修改 `Stock.vue` 頁面加入追蹤按鈕 | #3 |
| 10 | 修改 `ListItem.vue` 加入追蹤按鈕 | #3 |
| 11 | 修改 `CalendarDay.vue` 顯示追蹤標記 | #2 |
| 12 | 撰寫 `useWatchlist` 單元測試 | #2 |
| 13 | 撰寫 `WatchlistButton` 元件測試 | #3 |
| 14 | 手動驗證：加入/移除追蹤、切換頁面、持久化 | #8, #9, #10, #11 |

---

## 8. 驗收檢查清單

### 追蹤操作
- [ ] 在股票詳情頁可加入/移除追蹤
- [ ] 在列表模式可加入/移除追蹤
- [ ] 加入追蹤後 ❤️ 變為實心
- [ ] 移除追蹤後 ❤️ 變為空心
- [ ] 重複點擊不會重複加入

### 追蹤清單頁面
- [ ] 導覽列顯示追蹤清單連結
- [ ] 連結顯示追蹤數量徽章
- [ ] 點擊連結導航至 `/watchlist`
- [ ] 追蹤清單為空時顯示引導畫面
- [ ] 可切換行事曆/列表模式
- [ ] 行事曆正確標示追蹤股票的配息日期
- [ ] 列表正確顯示追蹤股票的配息資料

### 視覺標示
- [ ] 行事曆格子顯示股票代號（最多 3 支）
- [ ] 追蹤股票顯示代號 + ♥（紅色加粗）
- [ ] 非追蹤股票顯示代號（藍色）
- [ ] 超過 3 支顯示 +N
- [ ] 追蹤按鈕尺寸正確（sm/md/lg）
- [ ] 深色模式下樣式正常

### 持久化
- [ ] 刷新頁面後追蹤清單仍存在
- [ ] 關閉瀏覽器再開啟後追蹤清單仍存在
- [ ] 追蹤清單正確儲存至 localStorage

### 導航
- [ ] 從首頁可進入追蹤清單
- [ ] 從股票詳情頁可加入追蹤
- [ ] 從追蹤清單可返回首頁

### 測試覆蓋
- [ ] useWatchlist 單元測試通過
- [ ] WatchlistButton 元件測試通過
- [ ] 追蹤操作 E2E 測試通過

---

## 9. BDD Scenario 追溯對照表

| BDD Scenario | 對應組件/Composable | 對應規格章節 |
|---|---|---|
| 加入追蹤清單 | WatchlistButton + useWatchlist | §1.3, §1.4 |
| 移除追蹤清單 | WatchlistButton + useWatchlist | §1.3, §1.4 |
| 查看追蹤清單 | Watchlist.vue + WatchlistView | §1.5, §1.6 |
| 追蹤清單為空 | WatchlistEmpty | §1.6 |
| 追蹤清單行事曆模式 | WatchlistView + Calendar | §1.5 |
| 追蹤清單列表模式 | WatchlistView + ListView | §1.5 |
| 行事曆顯示股票代號 | CalendarDay + useWatchlist | §1.12 |
| 追蹤清單持久化 | useWatchlist + localStorage | §1.3, §2.1 |

---

## 📝 備註

- 追蹤清單為純前端功能，無後端 API 依賴
- 以證券代號（code）為主鍵，避免重複
- localStorage 有容量限制（約 5MB），追蹤清單不太可能超過
- 未來可擴展：匯出/匯入追蹤清單、雲端同步
- 通知功能（Phase 7）可擴展為僅通知追蹤清單中的股票
