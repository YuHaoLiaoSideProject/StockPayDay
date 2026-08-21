# 002 前端基礎（行事曆 + 列表） — UI/UX 設計文件

> **功能編號**：Phase 4
> **功能名稱**：前端基礎（行事曆 + 列表）
> **文件類型**：完整規格（單頁設計）
> **互動流程**：`docs/interaction-flows/phases/phase-4-前端基礎.md`
> **開發規格**：`docs/development/phases/phase-4-前端基礎.md`
> **狀態**：設計完成，待實作

---

## 1. 現況審計

### 1.1 現有元件分析

| # | 元件 | 位置 | 現狀 | 問題 |
|---|------|------|------|------|
| 1 | 行事曆 | 待新增 | 無 | 需從零設計 |
| 2 | 列表 | 待新增 | 無 | 需從零設計 |
| 3 | 模式切換 | 待新增 | 無 | 需從零設計 |
| 4 | 日期明細 Modal | 待新增 | 無 | 需從零設計 |
| 5 | 載入/錯誤/空狀態 | 待新增 | 無 | 需從零設計 |
| 6 | 深色模式切換 | 待新增 | 無 | 需從零設計 |

### 1.2 設計挑戰

| 挑戰 | 說明 | 解決方案 |
|------|------|---------|
| 行事曆日期格子觸控 | 小格子在手機上難以精準點擊 | 確保最小觸控目標 44px |
| 日期明細 Modal 關閉方式 | 點擊外部 + 按鈕雙關閉 | overlay click.self + close button |
| 深色模式切換流暢 | 切換時不閃爍 | 使用 CSS 變數 + transition |
| ViewSwitcher 語意 | Tab 切換需明確表達 | aria-selected + role="tablist" |
| 空狀態引導 | 無資料時需引導操作 | 提供重試按鈕 + 說明文案 |

---

## 2. 設計原則

| # | 原則 | 說明 |
|---|------|------|
| 1 | **一致性** | 行事曆與列表使用相同的色彩語言、間距、字級 |
| 2 | **漸進式揭露** | 先顯示核心資訊（日期、金額），點擊後顯示完整明細 |
| 3 | **Contextual 不佔位** | Modal 僅在需要時出現，不佔用常態空間 |
| 4 | **語意化圖示** | 📅 行事曆、📋 列表、📅 月份導航 |
| 5 | **即時回饋** | 模式切換即時、Modal 開關有過渡動畫 |

---

## 3. Design Token 表

### 3.1 尺寸

| Token | 值 | 用途 |
|-------|-----|------|
| `--h` | 36px | Desktop 控制元件高度 |
| `--h-mobile` | 44px | Mobile 控制元件高度 |
| `--calendar-cell` | 自動 (aspect-square) | 行事曆日期格子 |
| `--calendar-cell-min` | 44px | 行事曆格子最小寬度（觸控） |
| `--modal-max-w` | 400px | 日期明細 Modal 最大寬度 |

### 3.2 字級

| Token | 值 | 用途 |
|-------|-----|------|
| `--fs-page-title` | 1.25rem (20px) | 頁面標題 |
| `--fs-body` | 0.875rem (14px) | 內文字級 |
| `--fs-small` | 0.75rem (12px) | 輔助文字（星期標題、日期） |
| `--fs-calendar-day` | 0.8125rem (13px) | 行事曆日期數字 |
| `--fs-tab` | 0.8125rem (13px) | ViewSwitcher Tab 文字 |

### 3.3 圓角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-btn` | 6px | 按鈕 |
| `--radius-pill` | 18px | ViewSwitcher Tab |
| `--radius-modal` | 12px | Modal |
| `--radius-cell` | 8px | 行事曆日期格子 |

### 3.4 間距

| Token | 值 | 用途 |
|-------|-----|------|
| `--gap-xs` | 4px | 格子內間距 |
| `--gap-sm` | 8px | 元件內間距 |
| `--gap-md` | 16px | 元件間間距 |
| `--gap-lg` | 24px | 區塊間間距 |
| `--gap-xl` | 32px | 頁面邊距 |

### 3.5 色彩

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `--dividend-dot` | `#1a73e8` | `#60a5fa` | 配息圓點 |
| `--dividend-bg` | `#eff6ff` | `#1e3a5f` | 有配息日期背景 |
| `--today-ring` | `#1a73e8` | `#60a5fa` | 今天日期邊框 |
| `--tab-active-bg` | `#1a73e8` | `#60a5fa` | Tab active 背景 |
| `--tab-active-text` | `#ffffff` | `#ffffff` | Tab active 文字 |
| `--modal-overlay` | `rgba(0,0,0,0.5)` | `rgba(0,0,0,0.7)` | Modal 背景遮罩 |

### 3.6 動畫

| Token | 值 | 用途 |
|-------|-----|------|
| `--transition-fast` | `150ms ease` | Tab 切換、hover |
| `--transition-normal` | `200ms ease` | Modal 出現/消失 |
| `--transition-slow` | `300ms ease` | 頁面切換 |

---

## 4. 目標設計

### 4.1 行事曆模式 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++                        [☀️/🌙 切換]   │
├─────────────────────────────────────────────────────────┤
│ [📅 行事曆]  [📋 列表]                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ‹  2026 年 7 月  ›                                    │
│  ─────────────────────────────────────────────────────  │
│  日    一    二    三    四    五    六                  │
│  ─────────────────────────────────────────────────────  │
│       1     2     3     4     5                         │
│                                                         │
│  6     7     8     9    10    11    12                  │
│                                                         │
│ 13    14    15●   16    17    18●●  19                  │
│                   ● = 配息日                             │
│ 20    21    22    23    24    25    26                  │
│                                                         │
│ 27    28    29    30    31                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.2 列表模式 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++                        [☀️/🌙 切換]   │
├─────────────────────────────────────────────────────────┤
│ [📅 行事曆]  [📋 列表]                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  日期         代號       名稱         金額               │
│  ─────────────────────────────────────────────────────  │
│  2026-07-25   2330       台積電       $3.50             │
│  2026-07-28   0056       元大高股息   $2.10             │
│  2026-08-01   0050       元大台灣50   $1.80             │
│  2026-08-15   2317       鴻海         $4.20             │
│  ...                                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 日期明細 Modal Wireframe

```
┌─────────────────────────────────────────────────────────┐
│                         （遮罩層）                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  2026-07-25 配息股票              [✕]             │  │
│  │  ─────────────────────────────────────────────── │  │
│  │                                                   │  │
│  │  2330   台積電                    $3.50           │  │
│  │  2317   鴻海                      $4.20           │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 4.4 空狀態 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++                        [☀️/🌙 切換]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                      📋                                 │
│                                                         │
│             目前沒有即將配息的證券                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.5 錯誤狀態 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++                        [☀️/🌙 切換]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                      ⚠️                                 │
│                                                         │
│           資料載入失敗，請稍後再試                        │
│                                                         │
│                    [  重試  ]                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. 狀態矩陣

### 5.1 ViewSwitcher Tab 狀態

| 狀態 | 視覺 | 互動 | 備註 |
|------|------|------|------|
| **idle** | 灰色文字，透明背景 | hover 變色 | 未選中 Tab |
| **hover** | 文字變深，淺色背景 | 準備點擊 | 視覺回饋 |
| **focus** | 藍色 ring | 鍵盤可操作 | 無障礙 |
| **active** | 藍色背景 `var(--tab-active-bg)`，白色文字 | 當前選中 | aria-selected="true" |
| **disabled** | opacity: 0.5 | 不可點擊 | 載入中時 |

### 5.2 行事曆日期格子狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **普通日** | 白色背景，灰色文字 | hover 背景變色 |
| **其他月** | opacity: 0.4 | 可點擊（導航至該月） |
| **今天** | 藍色 ring 邊框 | 視覺標示 |
| **有配息** | 淺藍背景 + 藍色圓點 | 點擊開啟 Modal |
| **hover** | 背景色加深 | 準備點擊 |
| **focus** | 藍色 ring | 鍵盤可操作 |

### 5.3 日期明細 Modal 狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **開啟** | 半透明遮罩 + Modal 內容 | 點擊外部或 ✕ 關閉 |
| **關閉** | 不顯示 | - |
| **有配息** | 列表顯示股票代號、名稱、金額 | 點擊股票導航至詳情 |
| **無配息** | 顯示「該日無配息股票」 | 僅可關閉 |

### 5.4 全頁狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **loading** | spinner 動畫 + 「載入中...」 | 不可操作 |
| **success** | 顯示行事曆或列表 | 正常互動 |
| **error** | 錯誤訊息 + 重試按鈕 | 點擊重試 |
| **empty** | 空狀態引導 | 正常互動 |

---

## 6. RWD 行為表

| 斷點 | 行事曆 | 列表 | ViewSwitcher | Modal |
|------|--------|------|-------------|-------|
| **≥1024px** | 7 欄佈局，格子寬度自動 | 完整欄位（日期+代號+名稱+金額） | 水平排列 | 最大寬度 400px |
| **768–1023px** | 7 欄佈局 | 隱藏部分欄位 | 水平排列 | 最大寬度 360px |
| **≤767px** | 7 欄佈局，格子最小 44px | 僅顯示日期+代號+金額 | 全寬，Tab 高度 44px | 全寬（減去邊距） |

### 768px 以下細部行為

| 元件 | 行為 |
|------|------|
| Header | Logo + 深色模式切換（水平排列） |
| ViewSwitcher | 全寬，Tab 高度 44px，觸控友好 |
| 行事曆格子 | 最小寬度 44px，aspect-square |
| 列表 | 隱藏名稱欄，僅顯示日期+代號+金額 |
| Modal | 全寬（左右各 16px 邊距），觸控關閉 |

---

## 7. 無障礙清單

| WCAG 準則 | 要求 | 實作方式 |
|-----------|------|---------|
| 1.4.1 | 不以顏色單獨傳達 | 配息日用圓點 + 背景色雙重表達 |
| 2.5.5 | 觸控目標 ≥ 40px | 行事曆格子最小 44px，Tab 高度 44px |
| 2.4.7 | Focus ring 可見 | 所有可互動元素有 `focus:ring-2 focus:ring-accent` |
| 4.1.2 | ARIA tablist | ViewSwitcher 使用 `role="tablist"` + `aria-selected` |
| 4.1.2 | ARIA dialog | Modal 使用 `role="dialog"` + `aria-modal="true"` |
| 4.1.2 | ARIA live | 錯誤訊息使用 `aria-live="polite"` |

### 鍵盤操作

| 按鍵 | 行為 |
|------|------|
| `Tab` | 在 ViewSwitcher、行事曆格子、深色模式切換間移動 |
| `Enter` / `Space` | 點擊行事曆格子、切換 Tab、開啟 Modal |
| `Escape` | 關閉 Modal |
| `Arrow Left/Right` | 在 ViewSwitcher Tab 間移動 |
| `Arrow Up/Down` | 在行事曆格子間移動 |

---

## 8. 實作建議

### 8.1 元件結構

```
HomeView.vue
├── <header class="app-header">
│   ├── <h1> 標題
│   └── <button> 深色模式切換
├── <LoadingState> (v-if="status === 'loading'")
├── <ErrorState> (v-else-if="status === 'error'")
├── <EmptyState> (v-else-if="status === 'empty'")
└── <template v-else>
    ├── <ViewSwitcher> 模式切換
    ├── <Calendar> (v-if="calendar")
    ├── <ListView> (v-else)
    └── <DayDetail> (v-if="selectedDate")

Calendar.vue
├── <div class="calendar-header">
│   ├── <button> 上月
│   ├── <h2> 月份標題
│   └── <button> 下月
├── <div class="calendar-weekdays">
│   └── <div> × 7 星期標題
└── <div class="calendar-grid">
    └── <CalendarDay> × 35-42

CalendarDay.vue
└── <div class="calendar-day" :class="...">

DayDetail.vue
├── <div class="day-detail-overlay" @click.self>
│   └── <div class="day-detail-modal">
│       ├── <div class="modal-header">
│       │   ├── <h3> 日期標題
│       │   └── <button> 關閉
│       └── <ul> 配息列表
```

### 8.2 CSS 策略

```css
/* 行事曆 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
  min-width: 44px; /* 觸控目標 */
}

.calendar-day:hover {
  background: var(--surface-2);
}

.calendar-day.other-month {
  opacity: 0.4;
}

.calendar-day.is-today {
  border: 2px solid var(--today-ring);
  font-weight: 700;
}

.calendar-day.has-dividend {
  background: var(--dividend-bg);
}

.dividend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--dividend-dot);
  margin-top: 2px;
}

/* ViewSwitcher */
.view-switcher {
  display: inline-flex;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 3px;
  gap: 2px;
}

.view-switcher button {
  border: none;
  background: none;
  color: var(--muted);
  font-size: 0.8125rem;
  padding: 0.45rem 0.9rem;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-switcher button.active {
  background: var(--tab-active-bg);
  color: var(--tab-active-text);
}

/* Modal */
.day-detail-overlay {
  position: fixed;
  inset: 0;
  background: var(--modal-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}

.day-detail-modal {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.5rem;
  max-width: 400px;
  width: 90%;
  box-shadow: var(--shadow-lg);
}
```

### 8.3 動畫細節

| 動畫 | 屬性 | 說明 |
|------|------|------|
| Tab 切換 | `background`, `color` | 150ms ease |
| Modal 出現 | `opacity`, `transform` | 200ms ease，scale(0.95) → scale(1) |
| Modal 消失 | `opacity` | 150ms ease |
| 行事曆格子 hover | `background` | 150ms ease |
| 日期點擊 | `transform` | 150ms ease，scale(0.95) → scale(1) |

### 8.4 `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  .view-switcher button,
  .calendar-day,
  .day-detail-overlay,
  .day-detail-modal {
    transition: none;
  }
  .calendar-day:active,
  .day-detail-modal {
    transform: none;
  }
}
```

---

## 9. 驗收檢查清單

### 9.1 ViewSwitcher
- [ ] 兩個 Tab：行事曆、列表
- [ ] 點擊切換即時生效
- [ ] active 狀態視覺正確（藍底白字）
- [ ] aria-selected 狀態正確
- [ ] 鍵盤可操作（Tab + Enter/Space）
- [ ] focus ring 可見

### 9.2 行事曆
- [ ] 顯示當月月份標題
- [ ] 月份導航（上月/下月）正常
- [ ] 7 欄佈局正確
- [ ] 星期標題正確（日-六）
- [ ] 日期數字正確
- [ ] 其他月日期半透明
- [ ] 今天日期有 ring 邊框
- [ ] 有配息日期有圓點 + 背景色
- [ ] 點擊日期開啟 Modal
- [ ] 手機版格子可觸控（≥44px）

### 9.3 列表模式
- [ ] 依日期排序（近的在前）
- [ ] 顯示日期、代號、名稱、金額
- [ ] 金額綠色粗體
- [ ] 手機版隱藏名稱欄
- [ ] 點擊項目可導航（Phase 5）

### 9.4 日期明細 Modal
- [ ] 點擊日期開啟
- [ ] 顯示日期標題
- [ ] 顯示該日所有配息股票
- [ ] 點擊股票可導航（Phase 5）
- [ ] 無配息時顯示提示
- [ ] 點擊外部可關閉
- [ ] 點擊 ✕ 可關閉
- [ ] Escape 可關閉
- [ ] aria-modal 正確

### 9.5 狀態處理
- [ ] 載入中顯示 spinner
- [ ] 載入失敗顯示錯誤 + 重試
- [ ] 無資料顯示空狀態
- [ ] 重試按鈕可正常運作

### 9.6 深色模式
- [ ] 系統偏好偵測正常
- [ ] 手動切換正常
- [ ] localStorage 持久化正常
- [ ] 兩主題色彩可讀

### 9.7 響應式
- [ ] 手機版行事曆可正常使用
- [ ] 手機版列表可正常使用
- [ ] 手機版 Modal 可正常使用
- [ ] 平板版佈局正確

### 9.8 無障礙
- [ ] 鍵盤可操作所有功能
- [ ] Focus ring 可見
- [ ] ARIA 狀態正確
- [ ] 不以顏色單獨傳達

### 9.9 動畫
- [ ] Tab 切換動畫 150ms
- [ ] Modal 出現/消失動畫正常
- [ ] prefers-reduced-motion 適用

---

## 📝 備註

- 此設計文件為完整規格，無 BEFORE/AFTER 比較
- 設計 Token 與 Phase 5 保持一致
- HTML mockup 見 `docs/uiux/phase-4-前端基礎.html`
