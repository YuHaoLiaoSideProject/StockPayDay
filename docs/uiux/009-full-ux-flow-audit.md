# StockPayDay++ 全站操作流程 UI/UX 審計

> 審計日期：2026-08-24 ｜ 方法：程式碼全量走查（所有 Vue 組件 + CSS + composables）
> 審計範圍：Landing → Home（行事曆/列表）→ 單股歷史 → 追蹤清單 → 同步設定
> 參考基線：docs/uiux/現況UIUX審計與優化建議.md、006/007/008 設計文件

---

## 一、操作流程圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        使用者旅程                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ① Landing Page (#/)                                           │
│  ┌──────────────────────────────────────┐                      │
│  │  Hero → CTA「立即查看配息行事曆」     │                      │
│  │  How It Works（三步驟）→ CTA → Footer │                      │
│  └──────────┬───────────────────────────┘                      │
│             │ 點擊 CTA                                         │
│             ▼                                                   │
│  ② Home Page (#/app)                                           │
│  ┌──────────────────────────────────────┐                      │
│  │  Header: Logo │ ❤(追蹤) │ 🔍搜尋 │ 🌙暗色  │              │
│  │  ─────────────────────────────────── │                      │
│  │  ViewSwitcher: [📅行事曆] [📋列表]   │                      │
│  │                                       │                      │
│  │  ┌─ 行事曆模式 ──────────────────┐   │                      │
│  │  │  ‹ 2026年8月 ›               │   │                      │
│  │  │  日 一 二 三 四 五 六         │   │                      │
│  │  │  ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐│   │                      │
│  │  │  │  │  │  │23│  │25│  │  │  ││   │                      │
│  │  │  │  │  │  │4支│  │♥2│  │  │  ││   │                      │
│  │  │  └──┘└──┘└──┘└──┘└──┘└──┘└──┘│   │                      │
│  │  └───────────────────────────────┘   │                      │
│  │                                       │                      │
│  │  ┌─ 列表模式 ──────────────────┐     │                      │
│  │  │  日期 │ 代號 │ 名稱 │ 金額 │❤│   │                      │
│  │  │  ─────┼──────┼──────┼─────┼─│   │                      │
│  │  │ 8月25日（週一）        5支  │   │                      │
│  │  │ 2330   台積電    $4.50  ♡│   │                      │
│  │  └───────────────────────────────┘   │                      │
│  └─────┬──────────────┬────────────────┘                      │
│        │              │                                        │
│   點日期格子      點股票代號/名稱                               │
│        ▼              ▼                                        │
│  ③ DayDetail Modal    ④ StockView (#/stock/:code)              │
│  ┌──────────────┐    ┌──────────────────────────┐             │
│  │ 8月25日 配息  │    │ ← 返回              ♡    │             │
│  │ ──────────── │    │ ──────────────────────── │             │
│  │ 2330 台積電   │    │ 2330 台積電               │             │
│  │   $4.50      │    │ ──────────────────────── │             │
│  │ 2317 鴻海     │    │ 配息歷史                   │             │
│  │   $2.80      │    │ 年份 │ 除權息日 │ 金額     │             │
│  │              │    │ 2026 │ 08-25   │ $4.50    │             │
│  └──────────────┘    │ 2025 │ 08-20   │ $3.90    │             │
│        │              └──────────────────────────┘             │
│   點股票代號                                                     │
│        ▼                                                         │
│  ④ StockView                                                    │
│                                                                 │
│  ⑤ Watchlist Page (#/watchlist)                                  │
│  ┌──────────────────────────────────────┐                      │
│  │  ❤️ 我的追蹤清單                      │                      │
│  │  ─────────────────────────────────── │                      │
│  │  🔄 跨裝置同步（選配）                │                      │
│  │  [建立同步空間]  已有同步碼？直接貼上   │                      │
│  │  ─────────────────────────────────── │                      │
│  │  [📅行事曆] [📋列表]                   │                      │
│  │  ─────────────────────────────────── │                      │
│  │  （行事曆/列表，僅顯示追蹤股票）       │                      │
│  │  ─────────────────────────────────── │                      │
│  │  所有追蹤（N 支）                      │                      │
│  │  2330 台積電  $4.50  ♡               │                      │
│  │  2317 鴻海    $2.80  ♡               │                      │
│  └──────────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、各頁面審計發現

### 2.1 Landing Page（`LandingView.vue`）

**做得好的地方：**
- ✅ Hero → How It Works → CTA → Footer 結構清晰，符合 landing page 最佳實踐
- ✅ CTA 按鈕使用 `landing-btn-primary` 高對比色，引導明確
- ✅ How It Works 三步驟視覺引導，降低新使用者認知負擔
- ✅ Footer 包含功能介紹/開始使用/GitHub 連結
- ✅ Mobile RWD 完整：steps 縱向排列、CTA 全寬、section padding 收窄

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| L-1 | **Landing 頁缺少 Header 導覽** | P2 | Landing 頁有 sticky header（.landing-header），但僅含 Logo + 深色切換 + 一個 icon button（功能不明），缺少「開始使用」CTA 按鈕或導覽連結。首次訪客若已滾動至頁尾，需回頂端才能找到入口 |
| L-2 | **"了解更多 ↓" 錨點定位不精準** | P3 | `href="#how-it-works"` 使用 ID 錨點，但 Landing 頁為 hash mode routing（`/#/`），hash 錨點在 SPA 中可能行為不一致。實測中`#how-it-works` 在 hash mode 下可能跳轉至新頁面 |
| L-3 | **Social Proof 數據來源不明** | P3 | 「已追蹤超過 2,000 支股票」——此數據無後端支撐，為靜態文案。若實際資料量遠小於此，會降低可信度 |
| L-4 | **Footer GitHub 連結指向根目錄** | P3 | `href="https://github.com"` 未指向實際 repo URL，點擊後進入 GitHub 首頁而非專案頁面 |

---

### 2.2 Home Page — 行事曆模式（`HomeView.vue` + `Calendar.vue` + `CalendarDay.vue`）

**做得好的地方：**
- ✅ ViewSwitcher 使用 `role="tablist"` + `aria-selected`，符合 ARIA tabs pattern
- ✅ 行事曆格子顯示最多 3 支配息 +「+N」溢位提示，資訊密度適中
- ✅ 追蹤股票（watched）用紅色背景 +♥ 標示，與非追蹤股票有明確視覺區分
- ✅ 日期格子有 hover/focus 樣式（`.calendar-day:focus-visible` 用 inset box-shadow）
- ✅ Modal 日期格式本地化（「8月25日」而非 ISO 格式）

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| H-1 | **行事曆格子高度不均** | P2 | 無配息日 min-height=80px；有 3 支配息時高度膨脹至 ~120px（每支 label 18px + gap），造成行高不一致，掃讀困難。建議統一高度或限制最大高度 |
| H-2 | **配息 label 字級偏小** | P2 | `.dividend-label` 使用 `font-size: 0.68rem`（≈10.9px），對一般使用者偏小。建議提升至 `0.75rem`（12px） |
| H-3 | **月份導覽按鈕僅用 ‹ › 符號** | P3 | 單一三角符號辨識度低，建議改為「←」/「→」或「上月」/「下月」文字按鈕（或至少加 `aria-label="上個月"`/`aria-label="下個月"`） |
| H-4 | **行事曆無「回到今天」快速按鈕** | P3 | 當使用者翻到其他月份後，需手動翻回才能看到今天。建議在月份標題旁加「今天」按鈕（`.is-today` 標記已存在，只需定位） |

---

### 2.3 Home Page — 列表模式（`ListView.vue` + `ListItem.vue`）

**做得好的地方：**
- ✅ 日期分組（`groupedItems` computed）+ sticky date header，掃讀體驗佳
- ✅ 每組顯示「N 支」計數，提供摘要資訊
- ✅ 金額為 0 時顯示「—」而非裸 `$0.00`
- ✅ ListItem 使用 `tabindex="0"` + `@keydown.enter`，鍵盤可操作

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| LV-1 | **列表列的 WatchlistButton 與列點擊衝突** | P2 | ListItem 的 `@click` 經 `$emit('stock-click')` 導航至單股頁，但內嵌的 WatchlistButton 用 `@click.stop` 阻止冒泡。若 `@click.stop` 失效（如 touch 事件），會同時觸發導航。且愛心按鈕面積僅 32×32px，偏小 |
| LV-2 | **列表日期欄（.list-header 第一欄）在桌面版無實際內容** | P3 | `.list-header` 有「日期」欄位但 `.list-item` 第一欄為空 `<span></span>`，欄位浪費空間。建議移除日期欄或將日期分組 header 納入同一 grid |
| LV-3 | **列表無「回到今天」錨點** | P3 | 長列表中若要找最近日期的配息，需手動捲動。建議在列表頂部加「今天」或「最近」快捷錨點 |

---

### 2.4 DayDetail Modal（`DayDetail.vue`）

**做得好的地方：**
- ✅ 完整的 ARIA dialog 實作：`role="dialog"` + `aria-modal="true"` + `aria-labelledby`
- ✅ Focus trap（Tab 循環於 modal 內）+ Escape 關閉
- ✅ 背景 `overflow: hidden` 鎖定捲動
- ✅ `@click.self` 點擊遮罩關閉
- ✅ 日期本地化格式（「8月25日」）

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| MD-1 | **Modal 無關閉動畫** | P3 | 有 `modal-fade` transition 定義（opacity + scale），但 `.modal-overlay` 本身在 `v-if` 切換時可能跳過 transition（取決於父層 transition 名稱是否正確綁定）。實測中 transition name 為 `modal-fade`，與 CSS 定義一致，應可正常運作 |
| MD-2 | **Modal 列表無 hover/focus 樣式** | P3 | `.modal-list li` 有 `cursor: pointer` 但無 hover 背景色，使用者不易辨識可點擊區域。建議加 `:hover { background: var(--surface-2) }` |
| MD-3 | **Modal 空狀態訊息不一致** | P3 | 其他空狀態（WatchlistEmpty、EmptyState）有圖示 + 標題 + 描述 + 操作按鈕；Modal 空狀態僅有一行灰色文字「該日無配息股票」，風格不統一 |

---

### 2.5 StockView（`StockView.vue` + `StockDetail.vue`）

**做得好的地方：**
- ✅ 頂部有返回按鈕 + WatchlistButton，操作明確
- ✅ Loading/Error/Empty/Content 四態完整處理
- ✅ 歷史表格依年份降序排列，最新資料在最上方

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| SV-1 | **StockDetail 內部也有返回按鈕** | P2 | StockView 的 `.stock-top-bar` 已有「← 返回」按鈕，StockDetail 內部的 error/empty 狀態又各有一個「← 返回」，共計最多 3 個返回按鈕。建議：StockDetail 僅在 error/empty 狀態才顯示返回鈕，或完全移除由 StockView 統一處理 |
| SV-2 | **歷史表格缺少視覺層次** | P3 | 表格行間僅 1px border，無 zebra striping 或 hover 高亮（`.history-row:hover` 有定義但效果不明顯）。建議加 hover 背景色增強可讀性 |
| SV-3 | **歷史表格在手機隱藏除權息日** | P3 | `@media (max-width: 767px)` 隱藏 `.col-date`（用 `display: none`），但隱藏的是 table header，data column 用 `nth-child(2)` 選取——若表格結構變動會失效。建議改用 `.col-date` class 統一控制 |

---

### 2.6 WatchlistView（`WatchlistView.vue` + `WatchlistItemRow.vue`）

**做得好的地方：**
- ✅ 追蹤清單空狀態（WatchlistEmpty）提供明確引導：「搜尋股票」+「查看行事曆」
- ✅ 同步設定（WatchlistSyncSettings）功能完整：建立/配對/匯出匯入/停用
- ✅ 行事曆模式下方顯示「所有追蹤（N 支）」概覽

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| WL-1 | **WatchlistItemRow 樣式未納入全域 CSS** | P2 | WatchlistItemRow 使用 scoped style，但其 CSS 變數引用了未定義的 `--color-border`、`--color-hover`、`--color-text`、`--color-accent`、`--color-text-muted`，會 fallback 為硬編碼色值（#eee、#f5f5f5、#333、#e74c3c、#999），與專案 design token 不一致 |
| WL-2 | **追蹤清單行事曆日期點擊無反應** | P2 | `handleDateClick()` 在 WatchlistView 中定義但實作為空（僅 `selectedDate.value = date` 但 `getByDate` 結果被 `.filter(d => watchedCodes.value.has(d.code))` 過濾——若該日追蹤股票有配息則可正常顯示，但若無追蹤配息則打開空白 Modal） |
| WL-3 | **同步設定區在追蹤清單為空時仍顯示** | P3 | `WatchlistSyncSettings` 在 `<WatchlistEmpty v-if="isEmpty" />` 之前渲染，即使追蹤清單為空仍可操作同步設定。邏輯上合理（先設定同步再加追蹤），但視覺上 SYNC 設定區出現在空狀態上方，佔據空間 |
| WL-4 | **追蹤清單無排序控制** | P3 | `useWatchlist` 已支援 `sortBy`（addedAt/code/name/nextDividend），但 UI 未提供排序切換。預設按加入時間排序，若追蹤 50+ 支股票難以找到特定標的 |

---

### 2.7 Header / SearchBar（`App.vue` + `SearchBar.vue`）

**做得好的地方：**
- ✅ Mobile 搜尋改為 icon 展開模式（`isExpanded`），解決了之前 mobile header 重疊問題
- ✅ SearchBar 使用 `role="combobox"` + `aria-expanded` + `aria-autocomplete="list"`
- ✅ 搜尋結果列內嵌 WatchlistButton（slot 機制），解耦搜尋與追蹤邏輯
- ✅ Clear 按鈕有 `aria-label="清除搜尋"`

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| SB-1 | **搜尋結果無「查看更多」機制** | P3 | 結果限制 `.slice(0, 10)`，超過 10 筆時無提示「還有更多結果」。建議加「查看全部 N 筆」連結或分頁 |
| SB-2 | **搜尋無 loading 狀態** | P3 | `useSearch` 的 `securitiesIndex` 在 module 初始化時載入（fire-and-forget），若索引尚未載入完成，搜尋結果為空但無 loading indicator。建議在 `indexLoaded` 為 false 時顯示「載入中…」 |
| SB-3 | **Header icon button 尺寸不一致** | P3 | 追蹤清單 icon button 44×44px（`.header-icon-btn`）；theme-toggle 44×44px（`.theme-toggle`）；mobile 搜尋 icon button 44×44px——尺寸一致 ✓。但 `.header-icon-btn` 在 desktop 有 44px 高度而 `.search-input` 僅 36px，視覺上追蹤按鈕比搜尋框高 |

---

### 2.8 WatchlistSyncSettings（`WatchlistSyncSettings.vue`）

**做得好的地方：**
- ✅ 三態切換完整：未配對 → 已建立（顯示 token）→ 已配對（同步狀態）
- ✅ 匯出/匯入備援機制實作完整，格式錯誤有明確提示
- ✅ 複製 token 有 fallback（`document.execCommand('copy')`）
- ✅ 停用同步不刪除本地資料

**審計發現：**

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| SS-1 | **同步碼顯示無安全提示** | P3 | 同步碼（token）以 `<code>` 顯示且 `user-select: all`，但缺少「此碼相當於密碼，請勿分享給不信任的人」之類的安全提醒 |
| SS-2 | **匯出 textarea 設為 readonly 但無一鍵全選** | P3 | 匯出結果顯示在 `<textarea readonly>` 中，使用者需手動選取複製。建議加「全選」按鈕或自動選取 |
| SS-3 | **停用按鈕無二次確認** | P3 | 「停用」同步直接執行 `clearToken()`，無確認對話框。若誤觸需重新設定同步碼 |

---

## 三、跨頁面一致性問題

| # | 問題 | 嚴重度 | 說明 |
|---|------|--------|------|
| X-1 | **Design Token 不一致** | P2 | WatchlistItemRow 使用 scoped CSS 自定義變數（`--color-border`、`--color-accent` 等），與專案統一的 `--border`、`--tab-active-bg` 不同，導致深色模式下可能出現色彩不協調 |
| X-2 | **字級不一致** | P3 | 行事曆 label `0.68rem`、列表項目 `0.875rem`、同步設定描述 `0.8125rem`、landing 副標 `1.25rem`——字級跳躍缺乏系統性。建議建立統一 typography scale |
| X-3 | **圓角不一致** | P3 | 按鈕 `8px`（`.btn-primary`）、Modal `12px`（`.modal-content`）、SyncSettings `10px`（`.watchlist-sync-settings`）、Calendar header `6px`——無統一圓角 token |
| X-4 | **返回按鈕位置不一致** | P3 | StockView 返回鈕在 `.stock-top-bar`（flex space-between 左側）；StockDetail error/empty 狀態的返回鈕在內容中央。建議統一為頁面頂部左側 |

---

## 四、無障礙（Accessibility）審計

| WCAG 準則 | 狀態 | 說明 |
|-----------|------|------|
| 1.3.1 Info and Relationships | ⚠️ 部分通過 | ViewSwitcher 有 role=tablist ✓；SearchBar 有 role=combobox ✓；但 CalendarDay 無 role=button（div+@click） |
| 1.4.1 Use of Color | ✅ 通過 | 追蹤/非追蹤不只靠顏色，還有 ♥ 符號和背景色差異 |
| 1.4.3 Contrast (Minimum) | ⚠️ 部分通過 | --text-muted (#6b7280) 對白底 ≈4.7:1 ✓；但 --text-secondary 未獨立定義，部分 secondary 文字可能使用 --muted |
| 2.1.1 Keyboard | ⚠️ 部分通過 | Modal 有 focus trap ✓；ViewSwitcher 可 Tab ✓；但 CalendarDay（div+@click）無 tabindex，鍵盤無法操作行事曆格子 |
| 2.4.7 Focus Visible | ✅ 通過 | 所有互動元素有 `:focus-visible` 樣式（box-shadow ring） |
| 2.5.5 Target Size | ⚠️ 部分通過 | Header icon buttons 44px ✓；但 WatchlistButton--sm 僅 32px、WatchlistItemRow 內的愛心 32px |
| 4.1.2 Name, Role, Value | ✅ 通過 | SearchBar 有 aria-expanded/aria-autocomplete；WatchlistButton 有 aria-pressed/aria-label；Modal 有 aria-modal/aria-labelledby |

---

## 五、優化建議（依優先級）

### P1 — 建議立即處理

| # | 建議 | 影響範圍 |
|---|------|----------|
| A1 | **CalendarDay 加入鍵盤可操作性**：將 `.calendar-day` 改為 `<button>` 或加 `tabindex="0"` + `@keydown.enter` + `role="gridcell"` | CalendarDay.vue |
| A2 | **WatchlistItemRow 統一 Design Token**：移除 scoped CSS 中的自定義變數，改用專案統一的 `--border`、`--tab-active-bg`、`--text` 等 | WatchlistItemRow.vue |

### P2 — 建議近期處理

| # | 建議 | 影響範圍 |
|---|------|----------|
| B1 | **行事曆格子高度統一**：設定 `min-height: 80px; max-height: 96px`，超過 2 支配息時僅顯示前 2 支 +「+N」 | CalendarDay.vue + style.css |
| B2 | **配息 label 字級提升**：`.dividend-label` 從 `0.68rem` 提升至 `0.75rem`（12px），`.dividend-more` 從 `0.68rem` 提升至 `0.72rem` | style.css |
| B3 | **月份導覽加 aria-label**：`<button class="prev-month" aria-label="上個月">‹</button>` | Calendar.vue |
| B4 | **WatchlistItemRow 樣式整合**：將 scoped style 中的 CSS 變數替換為專案 design token，確保深色模式正確 | WatchlistItemRow.vue |
| B5 | **StockDetail 移除多餘返回按鈕**：error/empty 狀態的返回按鈕改為由 StockView 統一提供，或僅保留一個 | StockDetail.vue |
| B6 | **Modal 列表加 hover 樣式**：`.modal-list li:hover { background: var(--surface-2); cursor: pointer; }` | style.css |

### P3 — 建議後續處理

| # | 建議 | 影響範圍 |
|---|------|----------|
| C1 | **Landing Header 加入 CTA 按鈕**：在 landing-header-actions 加入「開始使用」小型按鈕 | LandingView.vue |
| C2 | **搜尋加 loading 狀態**：`indexLoaded` 為 false 時顯示 skeleton 或「載入中…」 | SearchBar.vue |
| C3 | **追蹤清單加排序控制**：在 WatchlistView 加入排序下拉選單（依加入時間/代號/名稱/下次配息） | WatchlistView.vue |
| C4 | **行事曆加「回到今天」按鈕**：在月份標題旁加「今天」按鈕 | Calendar.vue |
| C5 | **建立統一 Typography Scale**：0.75rem / 0.8125rem / 0.875rem / 1rem / 1.125rem / 1.25rem | style.css |
| C6 | **匯出 textarea 加「全選」按鈕**：一鍵選取所有匯出文字 | WatchlistSyncSettings.vue |
| C7 | **停用同步加確認對話框**：二次確認防止誤觸 | WatchlistSyncSettings.vue |
| C8 | **GitHub Footer 連結修正**：指向實際 repo URL | LandingView.vue |

---

## 六、驗收清單

- [ ] CalendarDay 可用 Tab 到達 + Enter/Space 觸發
- [ ] WatchlistItemRow 在深色模式下色彩正確
- [ ] 行事曆格子高度差異 ≤16px
- [ ] 配息 label 在一般螢幕上清晰可讀（≥12px）
- [ ] 月份導覽按鈕有 aria-label
- [ ] StockDetail error/empty 狀態最多 1 個返回按鈕
- [ ] Modal 列表項有 hover 背景反饋
- [ ] 全站 console error = 0（desktop + mobile、light + dark）

---

## 七、附錄：現有設計文件索引

| 編號 | 文件 | 範圍 |
|------|------|------|
| 006 | app-header-redesign | Header 重構（Logo + 搜尋 + 追蹤 + 深色切換） |
| 007 | homepage-commercial | Landing 頁商業化（Hero + How It Works + CTA + Footer） |
| 008 | landing-features-redesign | Landing 功能展示區重設計 |
| — | 現況UIUX審計與優化建議 | 初始全站審計（Phase 4-5 時期） |
