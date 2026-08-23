# Phase 8 優化打磨 — 開發規格

> **對應 Roadmap**：Phase 8 — `docs/roadmaps/phases.md` 項目 #11（RWD 響應式設計）+ #12（深色模式）
> **技術棧**：Vue 3.x · Vite 5.x · Tailwind CSS 3.x
> **操作流程**：`docs/interaction-flows/phases/phase-8-優化打磨.md`
> **BDD**：`docs/bdds/stockpayday.feature`
> **測試計畫**：`docs/test-plans/phases/phase-8-優化打磨測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

前端 RWD 響應式佈局、深色模式切換、體驗優化。核心包含：

1. **RWD 響應式佈局**：三段斷點（手機 <768px、平板 768–1024px、桌機 >1024px），所有元件自適應
2. **深色模式**：系統偏好偵測 + 手動切換 + localStorage 持久化
3. **體驗優化**：主題切換無閃爍、佈局即時調整無重載、載入動畫流暢

---

## BDD Scenario 追溯

| BDD Scenario | 對應規格章節 |
|--------------|-------------|
| 手機版顯示（viewport < 768px） | §2 RWD 響應式佈局、§7 CSS 關鍵樣式 |
| 平板版顯示（viewport 768–1024px） | §2 RWD 響應式佈局、§7 CSS 關鍵樣式 |
| 桌機版顯示（viewport > 1024px） | §2 RWD 響應式佈局、§7 CSS 關鍵樣式 |
| 偵測系統深色模式偏好 | §2 深色模式實作、§5 生命週期 |
| 偵測系統淺色模式偏好 | §2 深色模式實作、§5 生命週期 |
| 手動切換深色模式 | §2 深色模式實作、§7 CSS 關鍵樣式 |
| 手動切換淺色模式 | §2 深色模式實作、§7 CSS 關鍵樣式 |

---

## 1. 後端實作規格

**不適用** — Phase 8 為純前端優化，無後端改動。

---

## 2. 前端實作規格

### 2.1 檔案改動總覽

```
frontend/
├── tailwind.config.js              ← 修改：擴展深色模式 color token
├── src/
│   ├── style.css                   ← 修改：深色模式 CSS 變數、全域樣式
│   ├── main.js                     ← 修改：初始化深色模式偵測
│   ├── App.vue                     ← 修改：響應式導覽列、佈局容器
│   ├── composables/
│   │   └── useTheme.ts             ← 新增：深色模式偵測與切換
│   ├── stores/
│   │   └── theme.ts                ← 新增：Pinia theme store（持久化）
│   └── components/
│       ├── ThemeToggle.vue         ← 新增：深色模式切換按鈕
│       ├── Calendar.vue            ← 修改：RWD 響應式佈局
│       ├── ListView.vue            ← 修改：RWD 響應式佈局
│       ├── SearchBar.vue           ← 修改：RWD 搜尋欄樣式
│       └── StockDetail.vue         ← 修改：RWD 表格佈局
└── tests/
    └── e2e/
        ├── rwd.spec.ts             ← 新增：RWD E2E 測試
        └── dark-mode.spec.ts       ← 新增：深色模式 E2E 測試
```

### 2.2 tailwind.config.js — 深色模式與 color token 擴展

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',  // Phase 0 已預設
  theme: {
    extend: {
      colors: {
        // 深色模式 color token（使用 CSS 變數，動態切換）
        surface: {
          DEFAULT: 'var(--color-surface)',
          secondary: 'var(--color-surface-secondary)',
          hover: 'var(--color-surface-hover)',
        },
        text: {
          DEFAULT: 'var(--color-text)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
        },
        accent: {
          DEFAULT: 'var(--color-accent)',
          hover: 'var(--color-accent-hover)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
        },
      },
      // RWD 斷點（Tailwind 預設即可，此處明確列出供參考）
      screens: {
        'sm': '640px',
        'md': '768px',   // 手機/平板分界
        'lg': '1024px',  // 平板/桌機分界
        'xl': '1280px',
      },
    },
  },
  plugins: [],
}
```

### 2.3 style.css — 深色模式 CSS 變數定義

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ========== 淺色模式（預設） ========== */
:root {
  --color-surface: #ffffff;
  --color-surface-secondary: #f9fafb;
  --color-surface-hover: #f3f4f6;
  --color-text: #111827;
  --color-text-secondary: #4b5563;
  --color-text-muted: #9ca3af;
  --color-accent: #3b82f6;
  --color-accent-hover: #2563eb;
  --color-border: #e5e7eb;
}

/* ========== 深色模式 ========== */
.dark {
  --color-surface: #111827;
  --color-surface-secondary: #1f2937;
  --color-surface-hover: #374151;
  --color-text: #f9fafb;
  --color-text-secondary: #d1d5db;
  --color-text-muted: #6b7280;
  --color-accent: #60a5fa;
  --color-accent-hover: #3b82f6;
  --color-border: #374151;
}

/* ========== 全域基礎樣式 ========== */
body {
  @apply bg-surface text-text transition-colors duration-200;
}

/* ========== RWD: 手機行事曆 Grid ========== */
@media (max-width: 767px) {
  .calendar-grid {
    @apply text-xs;
  }
  .calendar-cell {
    @apply min-h-[3rem];
  }
}

/* ========== RWD: 平板行事曆 Grid ========== */
@media (min-width: 768px) and (max-width: 1023px) {
  .calendar-grid {
    @apply text-sm;
  }
  .calendar-cell {
    @apply min-h-[4rem];
  }
}

/* ========== RWD: 桌機行事曆 Grid ========== */
@media (min-width: 1024px) {
  .calendar-grid {
    @apply text-base;
  }
  .calendar-cell {
    @apply min-h-[5rem];
  }
}
```

### 2.4 composables/useTheme.ts — 深色模式偵測與切換

```typescript
/**
 * useTheme composable
 * 職責：偵測系統深色模式偏好、手動切換、持久化
 * 依賴：theme store (Pinia)
 */
import { ref, watch, onMounted } from 'vue'
import { useThemeStore } from '../stores/theme'

// localStorage key
const THEME_KEY = 'stockpayday-theme'

// 支援的主題模式
type ThemeMode = 'light' | 'dark' | 'system'

export function useTheme() {
  const store = useThemeStore()
  const systemDark = ref(false)       // 系統實際深色狀態
  const userPreference = ref<ThemeMode>('system')  // 使用者設定

  /**
   * 偵測系統深色模式偏好
   * 使用 matchMedia API
   */
  function detectSystemPreference(): boolean {
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  }

  /**
   * 應用主題到 DOM
   * 在 <html> 上新增/移除 dark class
   */
  function applyTheme(isDark: boolean): void {
    const html = document.documentElement
    if (isDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    store.setDarkMode(isDark)
  }

  /**
   * 根據使用者偏好 + 系統狀態決定實際主題
   */
  function resolveTheme(): boolean {
    if (userPreference.value === 'system') {
      return systemDark.value
    }
    return userPreference.value === 'dark'
  }

  /**
   * 切換深色/淺色模式
   */
  function toggleTheme(): void {
    const current = resolveTheme()
    const newMode: ThemeMode = current ? 'light' : 'dark'
    userPreference.value = newMode
    applyTheme(!current)
    savePreference(newMode)
  }

  /**
   * 設定主題模式（system/light/dark）
   */
  function setMode(mode: ThemeMode): void {
    userPreference.value = mode
    applyTheme(resolveTheme())
    savePreference(mode)
  }

  /**
   * 從 localStorage 讀取使用者偏好
   */
  function loadPreference(): void {
    const saved = localStorage.getItem(THEME_KEY) as ThemeMode | null
    if (saved && ['light', 'dark', 'system'].includes(saved)) {
      userPreference.value = saved
    }
  }

  /**
   * 儲存使用者偏好到 localStorage
   */
  function savePreference(mode: ThemeMode): void {
    localStorage.setItem(THEME_KEY, mode)
  }

  // 初始化
  onMounted(() => {
    // 1. 偵測系統偏好
    systemDark.value = detectSystemPreference()

    // 2. 載入使用者偏好
    loadPreference()

    // 3. 應用主題
    applyTheme(resolveTheme())

    // 4. 監聽系統偏好變化
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', (e) => {
        systemDark.value = e.matches
        // 僅在 system 模式下自動切換
        if (userPreference.value === 'system') {
          applyTheme(e.matches)
        }
      })
  })

  return {
    isDark: computed(() => store.isDarkMode),
    mode: userPreference,
    toggleTheme,
    setMode,
  }
}
```

### 2.5 stores/theme.ts — Pinia Theme Store

```typescript
/**
 * Theme Store
 * 職責：全域深色模式狀態管理
 * 持久化：由 useTheme composable 處理 localStorage
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // State
  const isDarkMode = ref(false)

  // Getters
  const currentTheme = computed(() => isDarkMode.value ? 'dark' : 'light')

  // Actions
  function setDarkMode(value: boolean): void {
    isDarkMode.value = value
  }

  function toggleDarkMode(): void {
    isDarkMode.value = !isDarkMode.value
  }

  return {
    isDarkMode,
    currentTheme,
    setDarkMode,
    toggleDarkMode,
  }
})
```

### 2.6 components/ThemeToggle.vue — 深色模式切換按鈕

```vue
<script setup lang="ts">
/**
 * ThemeToggle 深色模式切換按鈕
 * Props: 無
 * Emits: 無
 * 依賴：useTheme composable
 */
import { useTheme } from '../composables/useTheme'

const { isDark, toggleTheme } = useTheme()
</script>

<template>
  <button
    data-theme-toggle
    @click="toggleTheme"
    :aria-label="isDark ? '切換至淺色模式' : '切換至深色模式'"
    class="p-2 rounded-lg bg-surface-secondary hover:bg-surface-hover
           text-text-secondary transition-colors duration-200"
  >
    <!-- 太陽圖示（深色模式時顯示，點擊切至淺色） -->
    <svg v-if="isDark" xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0z" />
    </svg>
    <!-- 月亮圖示（淺色模式時顯示，點擊切至深色） -->
    <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" />
    </svg>
  </button>
</template>
```

### 2.7 App.vue — RWD 響應式佈局修改

```vue
<script setup lang="ts">
/**
 * App.vue 根元件
 * Phase 8 改動：
 * - 加入 RWD 響應式導覽列
 * - 加入 ThemeToggle 按鈕
 * - 調整佈局容器寬度
 */
import ThemeToggle from './components/ThemeToggle.vue'
</script>

<template>
  <div class="min-h-screen bg-surface">
    <!-- 導覽列 -->
    <header class="sticky top-0 z-50 bg-surface border-b border-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14 md:h-16">
          <!-- Logo + 標題 -->
          <div class="flex items-center gap-2">
            <span class="text-xl">📅</span>
            <h1 class="text-lg font-bold text-text">
              StockPayDay++
            </h1>
          </div>

          <!-- 右側：搜尋 + 主題切換 -->
          <div class="flex items-center gap-2">
            <SearchBar class="hidden sm:block" />
            <ThemeToggle />
          </div>
        </div>
      </div>

      <!-- 手機版搜尋欄（導覽列下方） -->
      <div class="sm:hidden px-4 pb-2">
        <SearchBar />
      </div>
    </header>

    <!-- 主要內容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <RouterView />
    </main>
  </div>
</template>
```

### 2.8 Calendar.vue — RWD 響應式行事曆

```vue
<script setup lang="ts">
/**
 * Calendar.vue 行事曆元件
 * Phase 8 改動：
 * - RWD Grid 佈局（手機 1 列、平板 2 列、桌機 7 列）
 * - 深色模式 color token
 */
// ... 現有邏輯

// RWD: 根據視窗寬度決定 Grid 行數
const gridCols = computed(() => {
  // Tailwind class binding
  return 'grid-cols-3 sm:grid-cols-5 lg:grid-cols-7'
})
</script>

<template>
  <div class="calendar-container">
    <!-- 月份標題 -->
    <div class="flex items-center justify-between mb-4">
      <button class="p-2 rounded hover:bg-surface-hover text-text-secondary">
        ←
      </button>
      <h2 class="text-lg font-semibold text-text">{{ currentYear }} 年 {{ currentMonth }} 月</h2>
      <button class="p-2 rounded hover:bg-surface-hover text-text-secondary">
        →
      </button>
    </div>

    <!-- 星期標題 -->
    <div class="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-7 gap-1 text-center text-text-muted text-xs mb-2">
      <div v-for="day in weekDays" :key="day" class="py-1">{{ day }}</div>
    </div>

    <!-- 行事曆格子 -->
    <div class="calendar-grid grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-7 gap-1">
      <div
        v-for="cell in calendarCells"
        :key="cell.date"
        class="calendar-cell p-1 sm:p-2 rounded cursor-pointer
               hover:bg-surface-hover transition-colors"
        :class="{ 'bg-surface-secondary': cell.isToday }"
        @click="onDateClick(cell.date)"
      >
        <div class="text-text-secondary text-xs">{{ cell.day }}</div>
        <!-- 配息標記 -->
        <div v-if="cell.dividends?.length" class="mt-1">
          <div
            v-for="div in cell.dividends.slice(0, 2)"
            :key="div.code"
            class="text-xs text-accent truncate"
          >
            {{ div.code }}
          </div>
          <div v-if="cell.dividends.length > 2" class="text-xs text-text-muted">
            +{{ cell.dividends.length - 2 }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 2.9 ListView.vue — RWD 列表佈局

```vue
<script setup lang="ts">
/**
 * ListView.vue 列表元件
 * Phase 8 改動：
 * - RWD: 手機隱藏部分欄位、桌機顯示完整欄位
 * - 深色模式 color token
 */
// ... 現有邏輯
</script>

<template>
  <div class="list-view">
    <!-- 桌機表頭 -->
    <div class="hidden lg:grid lg:grid-cols-4 gap-4 px-4 py-2 text-text-muted text-sm font-medium">
      <div>日期</div>
      <div>代號</div>
      <div>名稱</div>
      <div class="text-right">配息金額</div>
    </div>

    <!-- 列表項目 -->
    <div
      v-for="item in sortedItems"
      :key="item.code + item.ex_date"
      class="flex items-center justify-between px-4 py-3 border-b border-border
             hover:bg-surface-hover cursor-pointer transition-colors"
      @click="onItemClick(item.code)"
    >
      <!-- 手機版：僅顯示日期 + 代號 + 金額 -->
      <div class="flex items-center gap-3 lg:hidden">
        <span class="text-text-secondary text-sm">{{ item.ex_date }}</span>
        <span class="font-medium text-text">{{ item.code }}</span>
        <span class="text-accent font-semibold">${{ item.dividend }}</span>
      </div>

      <!-- 桌機版：顯示完整欄位 -->
      <div class="hidden lg:grid lg:grid-cols-4 gap-4 w-full text-text">
        <div>{{ item.ex_date }}</div>
        <div class="font-medium">{{ item.code }}</div>
        <div>{{ item.name }}</div>
        <div class="text-right font-semibold text-accent">${{ item.dividend }}</div>
      </div>
    </div>
  </div>
</template>
```

### 2.10 SearchBar.vue — RWD 搜尋欄

```vue
<script setup lang="ts">
/**
 * SearchBar.vue 搜尋欄元件
 * Phase 8 改動：
 * - RWD: 手機版全寬、桌機版固定寬度
 * - 深色模式 color token
 */
// ... 現有邏輯
</script>

<template>
  <div class="relative">
    <input
      v-model="query"
      type="text"
      placeholder="搜尋股票代號或名稱..."
      class="w-full sm:w-64 px-3 py-2 rounded-lg
             bg-surface-secondary text-text placeholder-text-muted
             border border-border focus:border-accent focus:outline-none
             transition-colors duration-200"
    />

    <!-- 搜尋結果下拉 -->
    <div
      v-if="query && results.length > 0"
      class="absolute top-full left-0 right-0 mt-1 bg-surface border border-border
             rounded-lg shadow-lg z-50 max-h-60 overflow-auto"
    >
      <div
        v-for="result in results"
        :key="result.code"
        class="px-4 py-2 hover:bg-surface-hover cursor-pointer text-text"
        @click="onResultClick(result.code)"
      >
        <span class="font-medium">{{ result.code }}</span>
        <span class="text-text-secondary ml-2">{{ result.name }}</span>
      </div>
    </div>

    <!-- 無結果提示 -->
    <div
      v-if="query && results.length === 0 && !loading"
      class="absolute top-full left-0 right-0 mt-1 bg-surface border border-border
             rounded-lg shadow-lg z-50 px-4 py-3 text-text-muted text-sm"
    >
      找不到符合的證券
    </div>
  </div>
</template>
```

### 2.11 main.js — 初始化深色模式偵測

```javascript
/**
 * main.js 入口
 * Phase 8 改動：
 * - App 掛載前先偵測系統偏好，避免閃爍
 * - 建立 Pinia 實例
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

// ===== Phase 8：避免深色模式閃爍 =====
// 在 App 掛載前，同步偵測系統偏好並套用
// 這樣頁面載入時就不會先顯示淺色再切換深色
;(function initThemeSync() {
  const THEME_KEY = 'stockpayday-theme'
  const saved = localStorage.getItem(THEME_KEY)
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  let isDark = false
  if (saved === 'dark') {
    isDark = true
  } else if (saved === 'light') {
    isDark = false
  } else {
    // system 或無設定 → 跟隨系統
    isDark = prefersDark
  }

  if (isDark) {
    document.documentElement.classList.add('dark')
  }
})()

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

---

## 3. API 合約

**不適用** — Phase 8 無新增或修改 API endpoint。

---

## 4. 資料流

```
[系統偏好偵測]
  matchMedia('(prefers-color-scheme: dark)')
       │
       ▼
[useTheme composable]
  ├── 讀取 localStorage('stockpayday-theme')
  ├── 決定初始主題（userPreference || systemDark）
  ├── applyTheme() → document.documentElement.classList.add/remove('dark')
  └── 監聽 matchMedia change event
       │
       ▼
[Pinia Theme Store]
  isDarkMode: boolean ← 被 useTheme 更新
       │
       ▼
[Vue Reactivity]
  .dark class on <html>
       │
       ▼
[CSS Variables]
  var(--color-surface), var(--color-text), ...
       │
       ▼
[Tailwind Utilities]
  bg-surface, text-text, ... ← 自動套用深色/淺色值
```

---

## 5. 生命週期

### 深色模式初始化流程

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 同步偵測 | `<script>` 執行（`main.js`） | 讀取 localStorage + matchMedia，同步套用 `.dark` class | `.dark` class 已套用到 `<html>` |
| App 掛載 | `app.mount('#app')` | Vue 生命週期開始 | App.vue 掛載完成 |
| Composable 初始化 | `useTheme()` 在 `App.vue` 呼叫 | 建立 reactive state、註冊 matchMedia listener | `onMounted` 完成 |
| 使用者互動 | 點擊 `ThemeToggle` | `toggleTheme()` → 套用 + 儲存 | localStorage 已更新 |

### RWD 佈局流程

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 首次載入 | 頁面載入 | Tailwind media query 自動套用對應 class | 佈局渲染完成 |
| 視窗改變 | `resize` event | CSS media query 自動切換 class（無 JS） | 佈局重新渲染 |

---

## 6. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| localStorage 不可用（隱私模式） | BDD Edge Case | catch 儲存失敗，降級為僅跟隨系統偏好 |
| matchMedia 不支援（舊瀏覽器） | BDD Edge Case | 降級為淺色模式，不顯示切換按鈕 |
| 深色模式切換失敗 | Interaction Flow §6 異常 | 保持當前主題，不影響功能 |
| RWD 佈局異常 | Interaction Flow §6 異常 | 調整視窗大小或重新整理 |
| 系統偏好動態切換 | BDD Scenario 偵測系統偏好 | 監聽 `change` event，僅在 system 模式下自動切換 |

---

## 7. CSS 關鍵樣式

| class / selector | 樣式重點 |
|-----------------|---------|
| `dark` | 設定在 `<html>`，觸發所有 CSS 變數切換 |
| `.dark .bg-surface` | 深色背景 `#111827` |
| `.dark .text-text` | 深色文字 `#f9fafb` |
| `.dark .border-border` | 深色邊框 `#374151` |
| `.calendar-grid` | RWD Grid：`grid-cols-3 sm:grid-cols-5 lg:grid-cols-7` |
| `.calendar-cell` | 最小高度依斷點調整（`min-h-[3rem/4rem/5rem]`） |
| `.list-view .lg\\:grid` | 桌機顯示完整欄位、手機隱藏 |
| `[data-theme-toggle]` | 切換按鈕，hover 狀態 |
| `transition-colors duration-200` | 主題切換過渡動畫 |
| `body` | `bg-surface text-text transition-colors` |

### Tailwind RWD 斷點對照

| 斷點 | Tailwind class prefix | 尺寸範圍 | 佈局策略 |
|------|----------------------|---------|---------|
| 手機 | (default) | < 768px | 行事曆 3 列、列表隱藏名稱欄、搜尋欄全寬 |
| 平板 | `sm:` / `md:` | 768–1024px | 行事曆 5 列、列表部分欄位、搜尋欄固定寬度 |
| 桌機 | `lg:` / `xl:` | > 1024px | 行事曆 7 列、列表完整欄位、導覽列橫向排列 |

---

## 8. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 修改 `tailwind.config.js`：新增 color token 定義 | - |
| 2 | 修改 `style.css`：新增 CSS 變數（淺色 + 深色）、RWD media query | #1 |
| 3 | 新增 `stores/theme.ts`：Pinia theme store | - |
| 4 | 新增 `composables/useTheme.ts`：深色模式偵測與切換 | #3 |
| 5 | 修改 `main.js`：同步偵測避免閃爍 | #2, #4 |
| 6 | 新增 `components/ThemeToggle.vue`：切換按鈕 | #4 |
| 7 | 修改 `App.vue`：加入 ThemeToggle、RWD 導覽列 | #6 |
| 8 | 修改 `Calendar.vue`：RWD Grid 佈局 + color token | #2 |
| 9 | 修改 `ListView.vue`：RWD 欄位顯隱 + color token | #2 |
| 10 | 修改 `SearchBar.vue`：RWD 寬度 + color token | #2 |
| 11 | 修改 `StockDetail.vue`：RWD 表格佈局 + color token | #2 |
| 12 | 手動測試：手機/平板/桌機三種佈局 | #7, #8, #9, #10, #11 |
| 13 | 手動測試：深色模式切換 + 持久化 | #6, #7 |
| 14 | 新增 E2E 測試：`rwd.spec.ts` | #12 |
| 15 | 新增 E2E 測試：`dark-mode.spec.ts` | #13 |

---

## 9. 基礎架構設定

**不適用** — Phase 8 無 Nginx / systemd / 環境變數變更。

---

## 10. 測試覆蓋矩陣

| BDD Scenario | E2E 測試 | 手動測試 | 視覺回歸 |
|--------------|:-------:|:-------:|:-------:|
| 手機版顯示 | `rwd.spec.ts` (viewport 375px) | ✅ | ✅ |
| 平板版顯示 | `rwd.spec.ts` (viewport 768px) | ✅ | ✅ |
| 桌機版顯示 | `rwd.spec.ts` (viewport 1920px) | ✅ | ✅ |
| 偵測系統深色模式偏好 | `dark-mode.spec.ts` (colorScheme: dark) | ✅ | ✅ |
| 偵測系統淺色模式偏好 | `dark-mode.spec.ts` (colorScheme: light) | ✅ | - |
| 手動切換深色模式 | `dark-mode.spec.ts` (toggle click) | ✅ | - |
| 手動切換淺色模式 | `dark-mode.spec.ts` (toggle click) | ✅ | - |

---

## 📝 備註

- 此階段為最後優化，完成後專案可交付
- RWD 和深色模式可獨立開發（建議先做深色模式，再做 RWD）
- 所有新增的 UI 元件使用 color token，確保深色模式一致
- CSS 過渡動畫使用 `transition-colors duration-200`，避免切換閃爍
- 手機版搜尋欄在 App.vue 中獨立處理（導覽列下方全寬顯示）
