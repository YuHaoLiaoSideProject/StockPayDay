# Phase 5 前端進階（單股歷史 + 搜尋） — 開發規格

> **對應 Roadmap**：Phase 5
> **技術棧**：Vue 3.x (Composition API) · Vite 5.x · Tailwind CSS 3.x
> **操作流程**：`docs/interaction-flows/phases/phase-5-前端進階.md`
> **BDD**：`docs/bdds/stockpayday.feature`
> **測試計畫**：`docs/test-plans/phases/phase-5-前端進階測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

實現單股歷史配息頁面與即時搜尋功能。核心包含：

1. **useStock composable**：載入單支證券歷史配息資料（`api/securities/{code}.json`）
2. **useSearch composable**：即時搜尋證券代號或名稱（`api/securities-index.json`）
3. **StockDetail 元件**：顯示股票代號、名稱、歷史配息表格（年份 / 除權息日 / 配息金額）
4. **SearchBar 元件**：搜尋輸入框 + 即時篩選結果下拉列表
5. **Stock view**：單股歷史頁面路由（`/stock/{code}`），含 Loading / Error / 空狀態處理

---

## 1. 前端實作規格

### 1.1 檔案改動總覽

```
frontend/src/
├── composables/
│   ├── useStock.ts              ← 新增：載入單股歷史資料
│   └── useSearch.ts             ← 新增：即時搜尋功能
├── components/
│   ├── StockDetail.vue          ← 新增：歷史配息表格元件
│   ├── SearchBar.vue            ← 新增：搜尋欄 + 結果下拉
│   ├── BackButton.vue           ← 新增：返回首頁按鈕
│   └── SearchBar.vue            ← 新增：搜尋欄元件
├── views/
│   └── Stock.vue                ← 新增：單股歷史頁面路由
├── router/
│   └── index.ts                 ← 修改：新增 /stock/:code 路由
└── stores/
    └── stocks.ts                ← 修改：新增 fetchSecuritiesIndex action
```

### 1.2 useStock composable

載入單支證券歷史配息資料。從 `api/securities/{code}.json` 讀取，回傳 stock 資料、loading 狀態、error 訊息。

```typescript
// frontend/src/composables/useStock.ts

import { ref, watchEffect } from 'vue'

/** 單筆歷史配息紀錄 */
interface DividendHistory {
  year: number
  ex_date: string
  dividend: number
}

/** 證券歷史配息資料 */
interface StockDetail {
  code: string
  name: string
  history: DividendHistory[]
}

/**
 * 載入單支證券歷史配息資料
 * @param code 證券代號
 */
export function useStock(code: Ref<string>) {
  const stock = ref<StockDetail | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  watchEffect(async () => {
    if (!code.value) return
    loading.value = true
    error.value = null
    stock.value = null

    try {
      const res = await fetch(`./api/securities/${code.value}.json`)
      if (!res.ok) {
        throw new Error('找不到該證券資料')
      }
      stock.value = await res.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '資料載入失敗'
    } finally {
      loading.value = false
    }
  })

  return { stock, loading, error }
}
```

### 1.3 useSearch composable

從 `api/securities-index.json` 載入證券清單，提供即時搜尋。支援代號與名稱模糊搜尋，結果限制 10 筆。

```typescript
// frontend/src/composables/useSearch.ts

import { ref, computed, watchEffect } from 'vue'

/** 證券索引項目 */
interface SecurityIndex {
  code: string
  name: string
}

/**
 * 即時搜尋證券
 * 從 securities-index.json 載入清單，提供 query ↔ results 雙向綁定
 */
export function useSearch() {
  const query = ref('')
  const securitiesIndex = ref<SecurityIndex[]>([])
  const indexLoaded = ref(false)

  // 載入證券索引（僅載入一次）
  watchEffect(async () => {
    if (indexLoaded.value) return
    try {
      const res = await fetch('./api/securities-index.json')
      if (res.ok) {
        securitiesIndex.value = await res.json()
        indexLoaded.value = true
      }
    } catch {
      // 索引載入失敗，搜尋功能降級
    }
  })

  /** 即時篩選結果（代號或名稱模糊匹配） */
  const results = computed(() => {
    if (!query.value.trim()) return []
    const q = query.value.trim().toLowerCase()
    return securitiesIndex.value
      .filter(s =>
        s.code.toLowerCase().includes(q) ||
        s.name.toLowerCase().includes(q)
      )
      .slice(0, 10) // 限制 10 筆
  })

  return { query, results }
}
```

### 1.4 StockDetail 元件

顯示單支證券歷史配息表格。含 Loading / Error / 空狀態處理。

```vue
<!-- frontend/src/components/StockDetail.vue -->

<script setup lang="ts">
interface DividendHistory {
  year: number
  ex_date: string
  dividend: number
}

interface Props {
  stock: {
    code: string
    name: string
    history: DividendHistory[]
  } | null
  loading: boolean
  error: string | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'back-click': []
}>()

/** 歷史資料依年份降序排列 */
const sortedHistory = computed(() => {
  if (!props.stock?.history) return []
  return [...props.stock.history].sort((a, b) => b.year - a.year)
})
</script>

<template>
  <!-- Loading State -->
  <div v-if="loading" class="loading-spinner">
    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    <span class="ml-2 text-gray-500">載入中...</span>
  </div>

  <!-- Error State -->
  <div v-else-if="error" class="error-message">
    <p class="text-red-500">{{ error }}</p>
    <button @click="emit('back-click')" class="back-button mt-4 text-blue-500 underline">
      ← 返回
    </button>
  </div>

  <!-- Empty State -->
  <div v-else-if="stock && sortedHistory.length === 0" class="empty-state">
    <p class="text-gray-500">暫無歷史配息資料</p>
    <button @click="emit('back-click')" class="back-button mt-4 text-blue-500 underline">
      ← 返回
    </button>
  </div>

  <!-- Stock Detail -->
  <div v-else-if="stock" class="stock-detail">
    <div class="flex items-center mb-4">
      <button @click="emit('back-click')" class="back-button text-blue-500 underline mr-4">
        ← 返回
      </button>
      <div>
        <span class="stock-code text-lg font-bold">{{ stock.code }}</span>
        <span class="stock-name ml-2 text-gray-600">{{ stock.name }}</span>
      </div>
    </div>

    <h2 class="text-lg font-semibold mb-2">配息歷史</h2>

    <table class="history-table w-full border-collapse">
      <thead>
        <tr class="border-b">
          <th class="text-left py-2">年份</th>
          <th class="text-left py-2">除權息日</th>
          <th class="text-right py-2">配息金額</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedHistory" :key="item.year" class="history-row border-b hover:bg-gray-50">
          <td class="py-2">{{ item.year }}</td>
          <td class="py-2">{{ item.ex_date }}</td>
          <td class="text-right py-2">${{ item.dividend.toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

### 1.5 SearchBar 元件

搜尋輸入框 + 即時篩選結果下拉列表。

```vue
<!-- frontend/src/components/SearchBar.vue -->

<script setup lang="ts">
interface SearchResult {
  code: string
  name: string
}

interface Props {
  results: SearchResult[]
  modelValue: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'select': [result: SearchResult]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const showDropdown = ref(false)

/** 輸入時更新 query 並顯示下拉 */
function onInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  emit('update:modelValue', value)
  showDropdown.value = true
}

/** 選擇搜尋結果 */
function onSelect(result: SearchResult) {
  emit('select', result)
  showDropdown.value = false
  emit('update:modelValue', '')
}

/** 點擊外部關閉下拉 */
function onClickOutside() {
  showDropdown.value = false
}
</script>

<template>
  <div class="search-bar relative" v-click-away="onClickOutside">
    <input
      ref="inputRef"
      type="text"
      :value="modelValue"
      @input="onInput"
      @focus="showDropdown = true"
      placeholder="搜尋股票代號或名稱..."
      class="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
    />

    <!-- 搜尋結果下拉 -->
    <div
      v-if="showDropdown && results.length > 0"
      class="search-results absolute w-full bg-white border rounded-lg shadow-lg mt-1 z-50 max-h-60 overflow-y-auto"
    >
      <div
        v-for="result in results"
        :key="result.code"
        @click="onSelect(result)"
        class="search-result-item px-4 py-2 hover:bg-gray-100 cursor-pointer flex justify-between"
      >
        <span class="font-medium">{{ result.code }}</span>
        <span class="text-gray-500">{{ result.name }}</span>
      </div>
    </div>

    <!-- 無結果提示 -->
    <div
      v-if="showDropdown && modelValue && results.length === 0"
      class="no-results absolute w-full bg-white border rounded-lg shadow-lg mt-1 z-50 px-4 py-3 text-gray-500"
    >
      找不到符合的證券
    </div>
  </div>
</template>
```

### 1.6 BackButton 元件

通用返回按鈕。

```vue
<!-- frontend/src/components/BackButton.vue -->

<script setup lang="ts">
const emit = defineEmits<{
  'click': []
}>()
</script>

<template>
  <button
    @click="emit('click')"
    class="back-button text-blue-500 hover:underline"
  >
    ← 返回
  </button>
</template>
```

### 1.7 Stock view（單股歷史頁面）

路由 `/stock/:code` 對應的頁面。整合 useStock、StockDetail、BackButton。

```vue
<!-- frontend/src/views/Stock.vue -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStock } from '@/composables/useStock'
import StockDetail from '@/components/StockDetail.vue'

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
    <StockDetail
      :stock="stock"
      :loading="loading"
      :error="error"
      @back-click="goBack"
    />
  </div>
</template>
```

### 1.8 Router 設定

新增 `/stock/:code` 路由。

```typescript
// frontend/src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Stock from '@/views/Stock.vue'

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
  ],
})

export default router
```

### 1.9 整合到 App.vue

在 App.vue 中整合 SearchBar 元件。

```vue
<!-- frontend/src/App.vue（修改摘要） -->

<script setup lang="ts">
import { useRouter } from 'vue-router'
import SearchBar from '@/components/SearchBar.vue'
import { useSearch } from '@/composables/useSearch'

const router = useRouter()
const { query, results } = useSearch()

function onStockSelect(result: { code: string; name: string }) {
  router.push(`/stock/${result.code}`)
  query.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Header -->
    <header class="p-4 border-b dark:border-gray-700">
      <div class="max-w-4xl mx-auto flex items-center justify-between">
        <h1 class="text-xl font-bold">📅 StockPayDay++</h1>
        <div class="w-64">
          <SearchBar
            v-model="query"
            :results="results"
            @select="onStockSelect"
          />
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

---

## 2. API / 資料合約

本專案為靜態站（GitHub Pages），前端直接 fetch JSON 檔案，無後端 API endpoint。

### 2.1 資料來源

| 檔案 | 路徑 | 用途 | 觸發時機 |
|------|------|------|---------|
| 證券歷史 | `api/securities/{code}.json` | 單股歷史配息資料 | 使用者點擊股票 |
| 證券索引 | `api/securities-index.json` | 搜尋用證券清單 | 首次搜尋時載入 |

### 2.2 資料格式

#### api/securities/{code}.json

```json
{
  "code": "2330",
  "name": "台積電",
  "history": [
    { "year": 2026, "ex_date": "2026-07-25", "dividend": 3.5 },
    { "year": 2025, "ex_date": "2025-07-18", "dividend": 3.2 },
    { "year": 2024, "ex_date": "2024-06-12", "dividend": 2.9 }
  ]
}
```

#### api/securities-index.json

```json
[
  { "code": "2330", "name": "台積電" },
  { "code": "0050", "name": "元大台灣50" },
  { "code": "0056", "name": "元大高股息" }
]
```

### 2.3 BDD Scenario 與資料對應

| BDD Scenario | 資料來源 | HTTP 狀態 |
|--------------|---------|-----------|
| 從行事曆查看單股歷史 | `api/securities/{code}.json` | 200 |
| 從列表查看單股歷史 | `api/securities/{code}.json` | 200 |
| 搜尋股票代號 | `api/securities-index.json` | 200 |
| 搜尋股票名稱 | `api/securities-index.json` | 200 |
| 點擊搜尋結果 | `api/securities/{code}.json` | 200 |
| 單股資料不存在 | `api/securities/{code}.json` | 404 |
| 搜尋無結果 | `api/securities-index.json` | 200（空陣列） |
| 歷史資料為空 | `api/securities/{code}.json` | 200（history 為空） |
| 網路斷線時顯示錯誤 | fetch 失敗 | Network Error |

---

## 3. 資料流

```
使用者點擊股票（行事曆/列表）
  │
  ├─→ Vue Router push(`/stock/${code}`)
  │     │
  │     └─→ Stock.vue (view)
  │           │
  │           └─→ useStock(code)
  │                 │
  │                 └─→ fetch(`./api/securities/${code}.json`)
  │                       │
  │                       ├─ 200 → stock.value = data → StockDetail 渲染
  │                       ├─ 404 → error.value = "找不到該證券資料"
  │                       └─ Network Error → error.value = "資料載入失敗"

使用者輸入搜尋關鍵字
  │
  ├─→ SearchBar (v-model → query)
  │     │
  │     └─→ useSearch()
  │           │
  │           └─→ fetch(`./api/securities-index.json`)（僅首次）
  │                 │
  │                 └─→ securitiesIndex.value = data
  │                       │
  │                       └─→ computed results = filter(query)
  │                             │
  │                             └─→ SearchBar 渲染下拉列表
  │                                   │
  │                                   └─→ 使用者點擊結果
  │                                         │
  │                                         └─→ Vue Router push(`/stock/${code}`)
  │                                               │
  │                                               └─→ 同上「單股歷史」流程
```

---

## 4. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| 單股資料不存在（404） | BDD @edge-case | 顯示「找不到該證券資料」錯誤訊息，附返回按鈕 |
| 網路斷線 | BDD @edge-case | 顯示「資料載入失敗」錯誤訊息 |
| 搜尋欄為空時 | BDD @edge-case | 不顯示搜尋結果下拉 |
| 歷史資料為空 | BDD @edge-case | 顯示「暫無歷史配息資料」提示，附返回按鈕 |
| 搜尋無結果 | BDD Scenario | 顯示「找不到符合的證券」提示 |
| 證券索引載入失敗 | Tech Decision | 搜尋功能降級（不顯示下拉），不影響其他功能 |
| 大量搜尋結果 | 互動流程 | 限制最多顯示 10 筆結果 |
| 搜尋大小寫 | 互動流程 | 代號與名稱搜尋忽略大小寫 |

---

## 5. CSS 關鍵樣式

| class | 樣式重點 |
|-------|---------|
| `.loading-spinner` | Flex 容器 + 動態旋轉動畫 (`animate-spin`) |
| `.error-message` | 紅色文字 + 返回按鈕 |
| `.empty-state` | 灰色文字 + 返回按鈕 |
| `.stock-detail` | 最大寬度 672px (`max-w-2xl`) + 水平置中 |
| `.stock-code` | 粗體、大字 |
| `.stock-name` | 灰色、正常字重 |
| `.history-table` | 全寬、框線分隔、hover 效果 |
| `.history-row` | 水平分隔線 + hover 背景變色 |
| `.search-bar` | 相對定位容器 |
| `.search-results` | 絕對定位下拉、陰影、最大高度可滾動 |
| `.search-result-item` | Flex 排列（代號 + 名稱）、hover 效果 |
| `.no-results` | 灰色文字、絕對定位下拉 |
| `.back-button` | 藍色文字 + hover 下底線 |

---

## 6. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 新增 useStock composable | - |
| 2 | 新增 useSearch composable | - |
| 3 | 新增 StockDetail 元件（含 Loading/Error/空狀態） | #1 |
| 4 | 新增 SearchBar 元件 | #2 |
| 5 | 新增 BackButton 元件 | - |
| 6 | 新增 Stock view | #3, #5 |
| 7 | 修改 router 新增 `/stock/:code` 路由 | #6 |
| 8 | 修改 App.vue 整合 SearchBar | #4, #7 |
| 9 | 撰寫 useStock 單元測試 | #1 |
| 10 | 撰寫 useSearch 單元測試 | #2 |
| 11 | 撰寫 StockDetail 元件測試 | #3 |
| 12 | 撰寫 SearchBar 元件測試 | #4 |
| 13 | 撰寫 E2E 測試（單股歷史 + 搜尋） | #8 |
| 14 | RWD 響應式調整 | #8 |

---

## 7. 驗收檢查清單

### 單股歷史頁面
- [ ] 點擊股票後導航至歷史頁面（URL 格式為 `/stock/{code}`）
- [ ] 顯示 Loading Spinner
- [ ] 正確顯示股票代號與名稱
- [ ] 歷史配息表格顯示：年份、除權息日、配息金額
- [ ] 歷史依年份排序（新→舊）
- [ ] 返回按鈕可回首頁
- [ ] 載入失敗顯示錯誤訊息
- [ ] 資料不存在顯示「找不到該證券資料」
- [ ] 歷史資料為空顯示「暫無歷史配息資料」

### 搜尋功能
- [ ] 搜尋欄可點擊取得焦點
- [ ] 可輸入股票代號搜尋（即時篩選）
- [ ] 可輸入股票名稱搜尋（即時篩選）
- [ ] 搜尋結果顯示：代號、名稱
- [ ] 點擊結果導航至歷史頁面
- [ ] 無結果時顯示「找不到符合的證券」提示
- [ ] 搜尋欄為空時不顯示下拉

### 導航
- [ ] 從首頁可導航至歷史頁面
- [ ] 從歷史頁面可返回首頁
- [ ] 從搜尋結果可導航至歷史頁面

### 響應式
- [ ] 手機版歷史頁面可正常顯示
- [ ] 手機版搜尋欄可正常使用

### 測試覆蓋
- [ ] useStock 單元測試通過
- [ ] useSearch 單元測試通過
- [ ] StockDetail 元件測試通過
- [ ] SearchBar 元件測試通過
- [ ] E2E 測試（單股歷史 + 搜尋）通過
