# 006 — app-header 重設計規格書

> **元件：** `app-header`（頂部導覽列）  
> **檔案位置：** `frontend/src/App.vue` + `frontend/src/style.css`  
> **日期：** 2025-08-23  
> **狀態：** Draft

---

## 1. 現況審計

| # | 問題 | 嚴重度 | 位置 | 影響 |
|---|------|--------|------|------|
| 1 | Header 高度 56px 偏大，與常見 48px 標準不符 | P2 | `.app-header` | 視覺比例失衡，壓縮內容區域空間 |
| 2 | Logo 區域與右側控制項視覺分組不明確 | P2 | `.header-left` / `.header-right` | 介面層級不清，使用者需額外認知負擔 |
| 3 | SearchBar 在 mobile 展開時 z-index 與 header 相同（40），可能被遮擋 | P1 | `.search-bar.expanded` | 搜尋結果可能被 header 遮擋，影響可用性 |
| 4 | 圖示按鈕與 SearchBar 之間缺乏視覺分隔 | P3 | `.header-icon-group` | 控制項邊界模糊，觸控時易誤觸 |
| 5 | Theme toggle 缺少 `aria-pressed` 狀態 | P2 | `.theme-toggle` | 輔助技術無法得知當前主題狀態 |
| 6 | Mobile 模式下 logo 文字隱藏但無 tooltip 補償 | P3 | `@media (max-width: 767px)` | 新使用者無法辨識品牌 |

---

## 2. 設計原則

沿用既有原則並擴展：

| # | 原則 | 說明 |
|---|------|------|
| 1 | **一致性** | 所有控制元件統一高度 `--header-height`、間距 `--header-gap`、圓角 `--radius-btn` |
| 2 | **漸進式揭露** | Mobile 隱藏非核心元素（logo 文字、分隔線），但保留 tooltip / aria 補償 |
| 3 | **Contextual 不佔位** | SearchBar 展開使用 `position: fixed` 覆蓋，不推擠其他元素 |
| 4 | **語意化圖示** | 所有 icon 使用 inline SVG + `aria-hidden="true"`，按鈕本體攜帶 `aria-label` |
| 5 | **觸控與鍵盤優先** | 觸控目標 ≥ 44×44px，focus ring 使用 `--focus-ring` token，寬度 3px |
| 6 | **層級清晰** | Header `z-index: 40`，SearchBar 展開 `z-index: 50`，確保下拉內容始終可見 |

---

## 3. 目標設計（Wireframe 描述）

### 3.1 Desktop（≥ 1024px）

```
┌─────────────────────────────────────────────────────────────────────┐
│  [≡] StockPayDay++    │  ─────  │  🔍 Search  │  ♡  │  🌙/☀️  │
│  Logo 區域            │  分隔線  │  SearchBar   │  追蹤  │  主題   │
└─────────────────────────────────────────────────────────────────────┘
         ← header-left →           ← header-right →
```

- 高度：48px（`--header-height`）
- Logo 區域與控制項之間：1px vertical 分隔線（`--border` 色）
- 圖示按鈕之間：8px 間距（`--header-gap`）
- SearchBar 寬度：256px

### 3.2 Tablet（768–1023px）

```
┌───────────────────────────────────────────────────┐
│  [≡] StockPayDay++  │  🔍 Search  │  ♡  │  🌙  │
└───────────────────────────────────────────────────┘
```

- 高度：48px
- 保留 logo 文字
- 分隔線保留
- SearchBar 寬度：200px

### 3.3 Mobile（≤ 767px）

```
┌──────────────────────────────┐
│  [≡]  │  🔍  │  ♡  │  🌙   │
└──────────────────────────────┘
```

- 高度：48px
- Logo 文字隱藏，icon 保留
- SearchBar 為 icon button，點擊後展開全寬搜尋欄
- 展開時 SearchBar 覆蓋 header 下方（`position: fixed; top: 48px`）

---

## 4. 狀態矩陣

### 4.1 Header Icon Button（追蹤清單、Theme Toggle）

| 狀態 | 背景 | 文字色 | Outline | 動畫 |
|------|------|--------|---------|------|
| **Idle** | `transparent` | `--text-muted` | none | — |
| **Hover** | `--surface-2` | `--text` | none | `background var(--transition-fast)` |
| **Focus** | `transparent` | `--text` | `box-shadow: 0 0 0 3px var(--focus-ring)` | — |
| **Active** | `--surface-2` | `--text` | none | — |
| **Disabled** | `transparent` | `--text-muted` @ 40% opacity | none | — |

### 4.2 Theme Toggle（含 aria-pressed）

| 狀態 | `aria-pressed` | 視覺回饋 |
|------|----------------|----------|
| 淺色模式 | `"false"` | 顯示月亮圖示 |
| 深色模式 | `"true"` | 顯示太陽圖示 + 背景 `--surface-2` |

### 4.3 SearchBar

| 狀態 | 框線 | 陰影 | 動畫 |
|------|------|------|------|
| **Idle** | `--border` | none | — |
| **Focus** | `--tab-active-bg` | `0 0 0 3px rgba(26,115,232,0.12)` | `border-color var(--transition-fast)` |
| **Expanded (Mobile)** | `--tab-active-bg` | `0 4px 12px rgba(0,0,0,0.1)` | slide-down 200ms |

### 4.4 Logo

| 狀態 | 視覺 |
|------|------|
| **Idle** | `--text` color, font-weight 600 |
| **Hover** | opacity 0.8 |
| **Mobile** | 文字 `display: none`，icon 保留，hover 時顯示 `title` tooltip |

---

## 5. RWD 行為表

| 斷點 | 高度 | Logo 文字 | 分隔線 | SearchBar 模式 | 圖示按鈕 | 間距 |
|------|------|-----------|--------|----------------|----------|------|
| **≥ 1024px** | 48px | 顯示 | 顯示 | 常駐輸入框 (256px) | 全部顯示 | 8px |
| **768–1023px** | 48px | 顯示 | 顯示 | 常駐輸入框 (200px) | 全部顯示 | 8px |
| **≤ 767px** | 48px | 隱藏 | 隱藏 | Icon → 展開全寬 | 全部顯示 | 4px |

### 5.1 Mobile SearchBar 展開行為

```
觸發： 點擊 search icon button
動畫： 從 header 下方 slide-down，200ms ease
定位： position: fixed; top: 48px; left: 0; right: 0
z-index: 50（高於 header 的 40）
關閉： 點擊 clear button / 選擇結果 / 點擊 header 外部
```

---

## 6. 無障礙清單（WCAG 2.1）

| WCAG SC | 要求 | 實作方式 |
|---------|------|----------|
| **1.4.1** Use of Color | 顏色不是唯一傳達資訊的方式 | Theme toggle 使用不同圖示（太陽/月亮）+ `aria-pressed`；watchlist badge 同時有數字 |
| **2.5.5** Target Size | 觸控目標 ≥ 44×44px | 所有 button 使用 `width: 44px; height: 44px`；SearchBar input 在 mobile 展開時 height 44px |
| **2.4.7** Focus Visible | 鍵盤使用者可見 focus indicator | 所有互動元素使用 `focus-visible` + `box-shadow: 0 0 0 3px var(--focus-ring)` |
| **4.1.2** Name, Role, Value | 自訂元件有正確的 ARIA 屬性 | Theme toggle `aria-pressed`；所有 icon `aria-hidden="true"`；按鈕有 `aria-label` |

### 6.1 ARIA 屬性規格

```html
<!-- Theme Toggle -->
<button
  class="theme-toggle"
  @click="toggleDark"
  :aria-pressed="isDark"
  :aria-label="isDark ? '切換為淺色模式' : '切換為深色模式'"
>
  <!-- SVG icon with aria-hidden="true" -->
</button>

<!-- Logo (mobile tooltip 補償) -->
<a class="app-logo" href="/" title="StockPayDay++">
  <svg aria-hidden="true">...</svg>
  <span class="logo-text">StockPayDay++</span>
</a>

<!-- Header Icon Buttons -->
<button class="header-icon-btn" aria-label="追蹤清單">
  <svg aria-hidden="true">...</svg>
</button>
```

---

## 7. 實作建議（CSS 變數調整）

### 7.1 新增 Design Tokens

```css
:root {
  /* Header 專用 tokens */
  --header-height: 48px;        /* 原 56px → 48px (P2 #1) */
  --header-gap: 8px;            /* 控制項之間距 */
  --header-gap-mobile: 4px;     /* Mobile 控制項之間距 */
  --header-divider: var(--border); /* 分隔線顏色 */
  --focus-ring: rgba(26, 115, 232, 0.4); /* Focus ring 顏色 */
  --radius-btn: 50%;            /* 圓形按鈕 */
}

.dark {
  --focus-ring: rgba(96, 165, 250, 0.4);
}
```

### 7.2 Header 重設計 CSS

```css
/* ============================================
   App Header — Redesign (006)
   ============================================ */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1rem;
  height: var(--header-height);  /* 48px */
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  position: sticky;
  top: 0;
  z-index: 40;
  gap: var(--header-gap);
}

/* Logo 區域 */
.header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
  flex-shrink: 1;
}

/* 控制項區域 */
.header-right {
  display: flex;
  align-items: center;
  gap: var(--header-gap);
  flex-shrink: 0;
}

/* 分隔線（Desktop/Tablet） */
.header-left::after {
  content: '';
  width: 1px;
  height: 24px;
  background: var(--header-divider);
  margin-left: 0.5rem;
  flex-shrink: 0;
}

/* Logo */
.app-logo {
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--text);
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
  min-width: 0;
  transition: opacity var(--transition-fast);
}

.app-logo:hover {
  opacity: 0.8;
}

/* Theme Toggle (P2 #5: aria-pressed) */
.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  width: 44px;
  height: 44px;
  padding: 0;
  border-radius: var(--radius-btn);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  transition: background var(--transition-fast), color var(--transition-fast);
}

.theme-toggle:hover {
  background: var(--surface-2);
  color: var(--text);
}

.theme-toggle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--focus-ring);
}

/* aria-pressed=true 時的視覺回饋 */
.theme-toggle[aria-pressed="true"] {
  color: var(--tab-active-bg);
}

/* ============================================
   RWD — Header
   ============================================ */

/* Tablet (768–1023px) */
@media (min-width: 768px) and (max-width: 1023px) {
  .header-left::after {
    display: block;
  }
  .search-bar {
    width: 200px;
  }
}

/* Mobile (≤ 767px) */
@media (max-width: 767px) {
  .app-header {
    gap: var(--header-gap-mobile);
  }

  .logo-text {
    display: none;
  }

  /* P3 #6: 隱藏文字但保留 tooltip */
  .app-logo {
    title: "StockPayDay++";
  }

  /* 隱藏分隔線 */
  .header-left::after {
    display: none;
  }

  /* SearchBar 展開 */
  .header-icon-group .search-bar {
    width: 0;
    position: static;
  }

  .header-icon-group .search-bar.expanded {
    width: 100vw;
    position: fixed;
    top: var(--header-height);  /* 使用 token */
    left: 0;
    right: 0;
    z-index: 50;  /* P1 #3: 確保高於 header */
    padding: 0.5rem 0.75rem;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .header-icon-group .search-bar.expanded .search-input {
    height: 44px;
    font-size: 1rem;
  }
}
```

### 7.3 Vue Template 調整

```vue
<!-- Theme Toggle: 新增 aria-pressed -->
<button
  class="theme-toggle"
  @click="toggleDark"
  :aria-pressed="isDark"
  :aria-label="isDark ? '切換為淺色模式' : '切換為深色模式'"
>
  <svg v-if="isDark" width="18" height="18" ... aria-hidden="true">...</svg>
  <svg v-else width="18" height="18" ... aria-hidden="true">...</svg>
</button>

<!-- Logo: 新增 title tooltip -->
<a
  href="javascript:void(0)"
  @click="() => router.push('/')"
  class="app-logo"
  title="StockPayDay++"
>
  <svg ... aria-hidden="true">...</svg>
  <span class="logo-text">StockPayDay++</span>
</a>
```

---

## 8. 驗收清單

### 8.1 視覺

- [ ] Header 高度改為 48px（`--header-height`）
- [ ] Logo 區域與控制項之間有垂直分隔線（Desktop/Tablet）
- [ ] 分隔線在 Mobile 隱藏
- [ ] 圖示按鈕之間間距統一（Desktop 8px, Mobile 4px）
- [ ] Theme toggle 在深色模式時有視覺差異（`aria-pressed="true"` 時高亮）

### 8.2 互動

- [ ] 所有按鈕 hover 時背景變為 `--surface-2`
- [ ] 所有按鈕 focus 時顯示 3px focus ring（`--focus-ring`）
- [ ] SearchBar 展開時 z-index (50) > header z-index (40)
- [ ] SearchBar 展開動畫 200ms ease
- [ ] Mobile SearchBar 展開不推擠其他元素

### 8.3 無障礙

- [ ] Theme toggle 有 `aria-pressed` 屬性
- [ ] Theme toggle 有 `aria-label`
- [ ] 所有 icon SVG 有 `aria-hidden="true"`
- [ ] Logo 在 Mobile 隱藏文字時有 `title` tooltip
- [ ] 觸控目標 ≥ 44×44px（使用 DevTools 驗證）
- [ ] 鍵盤 Tab 遷移順序：Logo → 追蹤清單 → SearchBar → Theme Toggle

### 8.4 RWD

- [ ] Desktop (≥ 1024px)：完整顯示 logo + 分隔線 + SearchBar
- [ ] Tablet (768–1023px)：完整顯示 logo + 分隔線 + SearchBar (200px)
- [ ] Mobile (≤ 767px)：logo 文字隱藏 + 分隔線隱藏 + SearchBar 為 icon

### 8.5 程式碼

- [ ] 所有硬編碼值改為 Design Token（`--header-height`, `--header-gap` 等）
- [ ] 沒有新增 console warning 或 error
- [ ] CSS 遵循現有命名慣例（BEM-like）

---

## 附錄：設計決策紀錄

| 決策 | 理由 | 替代方案 |
|------|------|----------|
| 高度從 56px 改為 48px | Material Design 3 標準 AppBar 高度；與 iOS 標準一致 | 保留 56px（但不符主流規範） |
| 分隔線使用 `::after` 偽元素 | 不佔用 HTML 結構，易於維護 | 使用 `<div class="divider">`（佔用 DOM） |
| z-index: 40/50 分層 | 確保 SearchBar 展開始終可見，未來可擴展 | 全部使用 50（但缺乏層級區分） |
| `aria-pressed` 而非 `aria-checked` | Toggle button 使用 pressed 語義更精確 | 使用 `aria-checked`（適合 switch 類型） |
| Mobile logo 用 `title` 而非 tooltip 元件 | 零額外 DOM，原生 tooltip 夠用 | 自訂 tooltip（增加複雜度） |
