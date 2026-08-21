# 003 前端進階（單股歷史 + 搜尋） — UI/UX 設計文件

> **功能編號**：Phase 5
> **功能名稱**：前端進階（單股歷史 + 搜尋）
> **文件類型**：完整規格（單頁設計）
> **互動流程**：`docs/interaction-flows/phases/phase-5-前端進階.md`
> **開發規格**：`docs/development/phases/phase-5-前端進階.md`
> **狀態**：設計完成，待實作

---

## 1. 現況審計

### 1.1 現有元件分析

| # | 元件 | 位置 | 現狀 | 問題 |
|---|------|------|------|------|
| 1 | 搜尋欄 | 待新增 | 無 | 需從零設計 |
| 2 | 股票歷史頁面 | 待新增 | 無 | 需從零設計 |
| 3 | 歷史配息表格 | 待新增 | 無 | 需從零設計 |
| 4 | 返回按鈕 | 待新增 | 無 | 需從零設計 |
| 5 | 搜尋結果下拉 | 待新增 | 無 | 需從零設計 |

### 1.2 設計挑戰

| 挑戰 | 說明 | 解決方案 |
|------|------|---------|
| 搜尋即時性 | 輸入即篩選，需快速回應 | 索引預載入 + computed 篩選 |
| 搜尋結果下拉 z-index | 可能被其他元素遮擋 | 設定 z-index: 50 |
| 搜尋無結果提示 | 需明確告知使用者 | 顯示「找不到符合的證券」 |
| 歷史表格 RWD | 手機版表格難以閱讀 | 關鍵欄位固定，其他隱藏 |
| 返回按鈕位置 | 需在多處出現 | 統一元件，一致樣式 |

---

## 2. 設計原則

| # | 原則 | 說明 |
|---|------|------|
| 1 | **一致性** | 搜尋欄、表格、按鈕使用相同的色彩語言、間距 |
| 2 | **漸進式揭露** | 搜尋結果下拉僅在有輸入時出現 |
| 3 | **Contextual 不佔位** | 搜尋結果下拉絕對定位，不佔用常態空間 |
| 4 | **語意化圖示** | 🔍 搜尋、← 返回、📅 配息日 |
| 5 | **即時回饋** | 搜尋結果即時更新、歷史資料即時載入 |

---

## 3. Design Token 表

### 3.1 尺寸

| Token | 值 | 用途 |
|-------|-----|------|
| `--h` | 36px | Desktop 控制元件高度 |
| `--h-mobile` | 44px | Mobile 控制元件高度 |
| `--search-max-w` | 256px | 搜尋欄最大寬度 |
| `--search-result-h` | 44px | 搜尋結果項高度 |
| `--stock-max-w` | 672px | 股票歷史頁面最大寬度 |

### 3.2 字級

| Token | 值 | 用途 |
|-------|-----|------|
| `--fs-page-title` | 1.25rem (20px) | 頁面標題 |
| `--fs-stock-code` | 1.125rem (18px) | 股票代號 |
| `--fs-body` | 0.875rem (14px) | 內文字級 |
| `--fs-small` | 0.75rem (12px) | 輔助文字 |
| `--fs-table-header` | 0.75rem (12px) | 表格標題 |
| `--fs-table-cell` | 0.8125rem (13px) | 表格內容 |

### 3.3 圓角

| Token | 值 | 用途 |
|-------|-----|------|
| `--radius-btn` | 6px | 按鈕 |
| `--radius-input` | 8px | 搜尋輸入框 |
| `--radius-dropdown` | 8px | 搜尋結果下拉 |
| `--radius-table` | 8px | 表格容器（可選） |

### 3.4 間距

| Token | 值 | 用途 |
|-------|-----|------|
| `--gap-xs` | 4px | 元件內間距 |
| `--gap-sm` | 8px | 元件內間距 |
| `--gap-md` | 16px | 元件間間距 |
| `--gap-lg` | 24px | 區塊間間距 |
| `--gap-xl` | 32px | 頁面邊距 |

### 3.5 色彩

| Token | Light | Dark | 用途 |
|-------|-------|------|------|
| `--search-focus` | `#1a73e8` | `#60a5fa` | 搜尋欄 focus 邊框 |
| `--search-focus-ring` | `rgba(26,115,232,0.12)` | `rgba(96,165,250,0.12)` | 搜尋欄 focus 光圈 |
| `--link-color` | `#1a73e8` | `#60a5fa` | 連結/返回按鈕 |
| `--link-hover` | `#1557b0` | `#93bbfd` | 連結 hover |
| `--table-border` | `#e3e6ea` | `#262e38` | 表格邊框 |
| `--table-hover` | `#f6f7f9` | `#1e2530` | 表格行 hover |
| `--amount-color` | `#188038` | `#34d399` | 金額文字（綠色） |
| `--error-color` | `#c5221f` | `#f87171` | 錯誤訊息 |
| `--muted-color` | `#9ca3af` | `#6b7280` | 輔助文字 |

### 3.6 動畫

| Token | 值 | 用途 |
|-------|-----|------|
| `--transition-fast` | `150ms ease` | hover 效果 |
| `--transition-normal` | `200ms ease` | 搜尋結果下拉 |
| `--transition-slow` | `300ms ease` | 頁面切換 |

---

## 4. 目標設計

### 4.1 搜尋欄 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  🔍 [ 搜尋股票代號或名稱...                      ]     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 2330   台積電                                     │  │
│  │ 0050   元大台灣50                                 │  │
│  │ 0056   元大高股息                                 │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  無結果時：                                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │            找不到符合的證券                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 4.2 股票歷史頁面 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++              [🔍 搜尋...]              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ← 返回                                                 │
│                                                         │
│  2330  台積電                                           │
│                                                         │
│  配息歷史                                               │
│  ─────────────────────────────────────────────────────  │
│  年份      除權息日        配息金額                      │
│  ─────────────────────────────────────────────────────  │
│  2026      2026-07-25      $3.50                        │
│  2025      2025-07-18      $3.20                        │
│  2024      2024-06-12      $2.90                        │
│  2023      2023-06-15      $2.75                        │
│  ...                                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.3 歷史資料為空 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++              [🔍 搜尋...]              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ← 返回                                                 │
│                                                         │
│  9999  測試股票                                         │
│                                                         │
│               📋                                        │
│                                                         │
│          暫無歷史配息資料                                │
│                                                         │
│              ← 返回                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.4 載入中 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++              [🔍 搜尋...]              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│                     ⏳                                  │
│                                                         │
│                  載入中...                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.5 錯誤狀態 Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ 📅 StockPayDay++              [🔍 搜尋...]              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ← 返回                                                 │
│                                                         │
│                ⚠️                                       │
│                                                         │
│         找不到該證券資料                                 │
│                                                         │
│              ← 返回                                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. 狀態矩陣

### 5.1 搜尋欄狀態

| 狀態 | 視覺 | 互動 | 備註 |
|------|------|------|------|
| **idle** | 灰色邊框，placeholder 顯示 | 可點擊輸入 | 預設狀態 |
| **focus** | 藍色邊框 `var(--search-focus)`，蓝色 ring | 準備輸入 | 無障礙 |
| **has-value** | 顯示 clear 按鈕 (✕) | 可清除輸入 | - |
| **has-results** | 下拉列表顯示 | 可選擇結果 | z-index: 50 |
| **no-results** | 下拉顯示「找不到符合的證券」 | 可修改關鍵字 | - |
| **loading** | input 右側 spinner | 等待搜尋結果 | - |
| **disabled** | opacity: 0.5 | 不可點擊 | 載入索引時 |

### 5.2 搜尋結果下拉狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **idle** | 不顯示 | - |
| **visible** | 絕對定位，陰影，最多 10 筆 | hover 變色 |
| **hover** | 背景色加深 | 準備點擊 |
| **focus** | 藍色 ring | 鍵盤可操作 |
| **selected** | 導航至股票詳情 | - |

### 5.3 歷史配息表格狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **loading** | spinner | 等待載入 |
| **success** | 表格顯示資料 | hover 行變色 |
| **error** | 錯誤訊息 + 返回按鈕 | 點擊返回 |
| **empty** | 「暫無歷史配息資料」+ 返回按鈕 | 點擊返回 |
| **hover** | 行背景色加深 | 視覺回饋 |

### 5.4 返回按鈕狀態

| 狀態 | 視覺 | 互動 |
|------|------|------|
| **idle** | 藍色文字 `← 返回` | hover 下底線 |
| **hover** | 藍色文字 + 下底線 | 準備點擊 |
| **focus** | 藍色 ring | 鍵盤可操作 |
| **active** | 文字變深 | 點擊返回首頁 |

---

## 6. RWD 行為表

| 斷點 | 搜尋欄 | 歷史表格 | 返回按鈕 | 頁面佈局 |
|------|--------|---------|---------|---------|
| **≥1024px** | 固定寬度 256px | 完整欄位（年份+日期+金額） | 文字連結 | 最大寬度 672px |
| **768–1023px** | 固定寬度 200px | 完整欄位 | 文字連結 | 最大寬度 672px |
| **≤767px** | 全寬 | 僅顯示年份+金額 | 文字連結 | 全寬（減去邊距） |

### 768px 以下細部行為

| 元件 | 行為 |
|------|------|
| Header | Logo + 搜尋圖示（全寬搜尋欄展開） |
| 搜尋欄 | 全寬，高度 44px |
| 歷史表格 | 隱藏除權息日欄，僅顯示年份+金額 |
| 返回按鈕 | 保持文字連結樣式 |
| 頁面邊距 | 左右各 16px |

---

## 7. 無障礙清單

| WCAG 準則 | 要求 | 實作方式 |
|-----------|------|---------|
| 1.4.1 | 不以顏色單獨傳達 | 金額用綠色 + 文字「$」雙重表達 |
| 2.5.5 | 觸控目標 ≥ 40px | 搜尋結果項高度 44px |
| 2.4.7 | Focus ring 可見 | 所有可互動元素有 `focus:ring-2 focus:ring-accent` |
| 4.1.2 | ARIA combobox | 搜尋欄使用 `role="combobox"` + `aria-expanded` |
| 4.1.2 | ARIA live | 搜尋結果使用 `aria-live="polite"` |
| 4.1.2 | ARIA label | 返回按鈕使用 `aria-label="返回首頁"` |

### 鍵盤操作

| 按鍵 | 行為 |
|------|------|
| `Tab` | 在搜尋欄、返回按鈕、表格間移動 |
| `Enter` / `Space` | 選擇搜尋結果、觸發返回按鈕 |
| `Escape` | 關閉搜尋結果下拉 |
| `Arrow Down/Up` | 在搜尋結果中移動 |
| `Arrow Left/Right` | 在表格欄位間移動（可選） |

---

## 8. 實作建議

### 8.1 元件結構

```
Stock.vue (view)
├── <div class="stock-view">
│   └── <StockDetail>

StockDetail.vue
├── <div v-if="loading"> LoadingSpinner
├── <div v-else-if="error"> ErrorMessage + BackButton
├── <div v-else-if="empty"> EmptyState + BackButton
└── <div v-else> StockContent
    ├── <div class="stock-header">
    │   ├── <BackButton>
    │   └── <div> 股票代號 + 名稱
    └── <table class="history-table">
        ├── <thead> 年份 | 除權息日 | 配息金額
        └── <tbody> 歷史資料行

SearchBar.vue
├── <div class="search-bar">
│   ├── <input> 搜尋輸入框
│   ├── <button> clear (✕)
│   └── <div class="search-results"> 搜尋結果下拉
│       └── <div> × N 筆結果

BackButton.vue
└── <button class="back-button"> ← 返回
```

### 8.2 CSS 策略

```css
/* 搜尋欄 */
.search-bar {
  position: relative;
  max-width: var(--search-max-w);
}

.search-bar input {
  width: 100%;
  height: var(--h);
  padding: 0 3rem 0 2.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-input);
  background: var(--surface);
  color: var(--text);
  font-size: var(--fs-body);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-bar input:focus {
  border-color: var(--search-focus);
  box-shadow: 0 0 0 3px var(--search-focus-ring);
  outline: none;
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-dropdown);
  box-shadow: var(--shadow-lg);
  margin-top: 4px;
  max-height: 240px;
  overflow-y: auto;
  z-index: 50;
}

.search-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: background 0.15s ease;
  height: var(--search-result-h);
}

.search-result-item:hover {
  background: var(--surface-2);
}

/* 歷史表格 */
.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-table-cell);
}

.history-table th {
  font-size: var(--fs-table-header);
  color: var(--muted);
  font-weight: 600;
  text-align: left;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--table-border);
}

.history-table td {
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--table-border);
}

.history-table tr:hover {
  background: var(--table-hover);
}

.history-table .amount {
  color: var(--amount-color);
  font-weight: 600;
  text-align: right;
}

/* 返回按鈕 */
.back-button {
  background: none;
  border: none;
  color: var(--link-color);
  cursor: pointer;
  font-size: var(--fs-body);
  padding: 0;
  text-decoration: none;
  transition: color 0.15s ease;
}

.back-button:hover {
  color: var(--link-hover);
  text-decoration: underline;
}

.back-button:focus-visible {
  outline: 2px solid var(--search-focus);
  outline-offset: 2px;
  border-radius: 4px;
}

/* 股票標題 */
.stock-code {
  font-size: var(--fs-stock-code);
  font-weight: 700;
  color: var(--text);
}

.stock-name {
  font-size: var(--fs-body);
  color: var(--muted);
  margin-left: 0.5rem;
}
```

### 8.3 動畫細節

| 動畫 | 屬性 | 說明 |
|------|------|------|
| 搜尋結果下拉 | `opacity`, `transform` | 200ms ease，translateY(-8px) → translateY(0) |
| 搜尋結果 hover | `background` | 150ms ease |
| 歷史表格行 hover | `background` | 150ms ease |
| 返回按鈕 hover | `text-decoration` | 150ms ease |
| 頁面載入 | `opacity` | 300ms ease |

### 8.4 `prefers-reduced-motion`

```css
@media (prefers-reduced-motion: reduce) {
  .search-bar input,
  .search-results,
  .search-result-item,
  .history-table tr,
  .back-button {
    transition: none;
  }
  .search-results {
    transform: none;
  }
}
```

---

## 9. 驗收檢查清單

### 9.1 搜尋欄
- [ ] 可點擊取得焦點
- [ ] 可輸入股票代號搜尋
- [ ] 可輸入股票名稱搜尋
- [ ] 即時顯示搜尋結果（≤10 筆）
- [ ] 搜尋結果含代號、名稱
- [ ] 點擊結果導航至歷史頁面
- [ ] 無結果時顯示提示
- [ ] 搜尋欄為空時不顯示下拉
- [ ] Escape 可關閉下拉
- [ ] 清除按鈕可清除輸入
- [ ] focus ring 可見
- [ ] aria-expanded 狀態正確

### 9.2 股票歷史頁面
- [ ] 點擊股票後導航至歷史頁面
- [ ] URL 格式為 `/stock/{code}`
- [ ] 顯示 Loading Spinner
- [ ] 正確顯示股票代號與名稱
- [ ] 歷史配息表格顯示：年份、除權息日、配息金額
- [ ] 歷史依年份排序（新→舊）
- [ ] 返回按鈕可回首頁
- [ ] 載入失敗顯示錯誤訊息
- [ ] 資料不存在顯示「找不到該證券資料」
- [ ] 歷史資料為空顯示「暫無歷史配息資料」

### 9.3 歷史表格
- [ ] 表格標題正確（年份、除權息日、配息金額）
- [ ] 資料行正確顯示
- [ ] 金額綠色粗體
- [ ] hover 行變色
- [ ] 手機版隱藏除權息日欄

### 9.4 返回按鈕
- [ ] 顯示「← 返回」
- [ ] 點擊可回首頁
- [ ] hover 有下底線
- [ ] focus ring 可見
- [ ] aria-label 正確

### 9.5 導航
- [ ] 從首頁可導航至歷史頁面
- [ ] 從歷史頁面可返回首頁
- [ ] 從搜尋結果可導航至歷史頁面

### 9.6 響應式
- [ ] 手機版歷史頁面可正常顯示
- [ ] 手機版搜尋欄可正常使用
- [ ] 手機版表格可正常閱讀
- [ ] 平板版佈局正確

### 9.7 無障礙
- [ ] 鍵盤可操作所有功能
- [ ] Focus ring 可見
- [ ] ARIA 狀態正確
- [ ] 不以顏色單獨傳達

### 9.8 動畫
- [ ] 搜尋下拉動畫 200ms
- [ ] 表格行 hover 動畫 150ms
- [ ] prefers-reduced-motion 適用

---

## 📝 備註

- 此設計文件為完整規格，無 BEFORE/AFTER 比較
- 設計 Token 與 Phase 4 保持一致
- HTML mockup 見 `docs/uiux/phase-5-前端進階.html`
