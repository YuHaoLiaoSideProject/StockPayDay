# 007 — 首頁商業化重設計規格書

> **頁面：** 首頁（`/#/`）  
> **檔案位置：** `frontend/src/views/LandingView.vue` + `frontend/src/style.css`  
> **日期：** 2025-08-24  
> **狀態：** Draft

---

## 1. 現況審計

### 1.1 首頁目前狀態

| # | 問題 | 嚴重度 | 位置 | 證據 |
|---|------|--------|------|------|
| 1 | **README 風格 ≠ 商業產品**：首頁展示 `python -m venv`、`npm install` 等開發指令，面向開發者而非投資人 | P1 | `LandingView.vue` `<pre><code>` 區塊 | 程式碼走查：`pip install -r requirements.txt`、`cd frontend`、`npm run dev` |
| 2 | **缺乏價值主張（Value Proposition）**：副標題僅「提醒投資人股利發放日期的工具」一句話，未回答「為什麼要使用」 | P1 | `LandingView.vue` `.subtitle` | 程式碼走查 |
| 3 | **無 Hero Section**：進入首頁直接看到 h1 + 功能列表，無視覺吸引力、無引導動線 | P1 | `LandingView.vue` template | 程式碼走查 |
| 4 | **CTA 按鈕不起眼**：「進入股票配息行事曆 →」按鈕與周圍缺乏視覺層級，無 secondary CTA（如「了解更多」） | P2 | `.cta` 樣式 | CSS 走查：僅單一蓝色按鈕 |
| 5 | **無 Social Proof**：無使用者數據、無口碑推薦、無「已有 N 人使用」等信任元素 | P2 | `LandingView.vue` | 程式碼走查：全文無任何數據 |
| 6 | **無 Feature Highlight 視覺**：功能列表以 `<ul>` 文字呈現，無圖示、無卡片、無動畫 | P2 | `LandingView.vue` `<ul>` 區塊 | 程式碼走查 |
| 7 | **無 Footer 導覽**：footer 僅一行版權聲明，無連結至功能頁、GitHub、聯絡方式 | P3 | `LandingView.vue` `<footer>` | 程式碼走查 |
| 8 | **LandingView 與 App 路由脫節**：`LandingView` 存在但 router 中 `/` 指向 `HomeView`（行事曆），LandingView 實際未被使用 | P1 | `router/index.ts` | `path: '/', component: HomeView` |
| 9 | **首頁無 RWD 考量**：`.landing-container` 固定 `max-width: 800px`，在 mobile 與 desktop 無差異化設計 | P2 | `LandingView.vue` scoped CSS | CSS 走查 |
| 10 | **無深色模式適配**：LandingView 的 scoped CSS 硬編碼 `#0d1117`、`#161b22` 等色值，未使用 CSS 變數 | P3 | `LandingView.vue` scoped CSS | CSS 走查 |

### 1.2 與商業化產品的差距分析

| 維度 | 現況 | 商業化標準 | 差距 |
|------|------|-----------|------|
| **價值傳達** | 技術功能描述 | 用戶利益導向 | 🔴 嚴重 |
| **視覺吸引力** | 純文字 + code block | Hero 圖 + 動畫 + 色彩 | 🔴 嚴重 |
| **信任建立** | 無 | 數據 + 評價 + 品牌 | 🔴 嚴重 |
| **行動引導** | 單一 CTA | 多層次 CTA（Primary + Secondary） | 🟡 中等 |
| **資訊架構** | README 結構 | 行銷漏斗結構 | 🔴 嚴重 |
| **響應式設計** | 無 | Mobile-first | 🟡 中等 |
| **品牌一致性** | 無設計語言 | 統一 Token + 色彩系統 | 🟡 中等 |

---

## 2. 設計原則

| # | 原則 | 說明 | 實作指引 |
|---|------|------|----------|
| 1 | **用戶利益優先** | 每個功能描述回答「這對你有什麼好處」，而非「這是什麼技術」 | 「提醒你不錯過任何股利」取代「從 TWSE 抓取資料」 |
| 2 | **漸進式揭露** | 首屏只顯示核心價值，滾動才看更多細節 | Hero → Features → Social Proof → CTA |
| 3 | **信任建立** | 用數據、視覺化、品牌一致性建立可信度 | 「已追蹤 N 支股票」+ 專業配色 + 統一圖示 |
| 4 | **Mobile-First** | 從 375px 起設計，向上拓展 | Hero 圖在 mobile 縮為插圖，desktop 用截圖 |
| 5 | **可及性** | WCAG 2.1 AA 合規 | 對比 ≥ 4.5:1、focus ring、aria-label |

---

## 3. 目標設計

### 3.1 頁面結構（Wireframe）

```
┌─────────────────────────────────────────────────────────┐
│  Header (已有，保留 Search + Theme + Watchlist)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─── Hero Section ──────────────────────────────────┐  │
│  │                                                   │  │
│  │  [Icon/插圖]                                       │  │
│  │                                                   │  │
│  │  你的股利，不再錯過。                                │  │
│  │  StockPayDay 幫你掌握每一筆配息時程。                │  │
│  │                                                   │  │
│  │  [📅 立即查看配息行事曆]  [了解更多 ↓]              │  │
│  │                                                   │  │
│  │  ★ 已追蹤超過 2,000 支股票的配息時程                │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─── Features Section ──────────────────────────────┐  │
│  │                                                   │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐           │  │
│  │  │ 📅      │  │ 🔍      │  │ ♡       │           │  │
│  │  │ 配息行事曆│  │ 即時搜尋 │  │ 追蹤清單 │           │  │
│  │  │ 一目了然 │  │ 快速找到 │  │ 跨裝置同步│           │  │
│  │  │ 配息日期  │  │ 你關注的 │  │ 隨時掌握 │           │  │
│  │  └─────────┘  └─────────┘  └─────────┘           │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─── How It Works Section ──────────────────────────┐  │
│  │                                                   │  │
│  │  ① 搜尋股票  →  ② 加入追蹤  →  ③ 掌握時程         │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─── CTA Section ───────────────────────────────────┐  │
│  │                                                   │  │
│  │  準備好了嗎？                                      │  │
│  │  [📅 開始使用]                                     │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─── Footer ────────────────────────────────────────┐  │
│  │  StockPayDay++ © 2026                             │  │
│  │  [GitHub] [功能] [聯絡我們]                        │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Hero Section 詳細設計

#### Desktop（≥ 1024px）

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     你的股利，不再錯過。                                        │
│     StockPayDay 幫你掌握每一筆配息時程。                        │
│                                                              │
│     [📅 立即查看配息行事曆]   [了解更多 ↓]                     │
│                                                              │
│     ★ 已追蹤超過 2,000 支股票的配息時程                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 標題字級：`2.5rem`（40px），font-weight 700
- 副標題字級：`1.25rem`（20px），color `--text-secondary`
- CTA 按鈕：高度 48px，padding 0 32px，border-radius 12px
- 社會證明：小字 `0.875rem`，color `--text-muted`，帶星號圖示

#### Mobile（≤ 767px）

```
┌───────────────────────┐
│                       │
│  你的股利，不再錯過。   │
│  幫你掌握配息時程。     │
│                       │
│  [📅 立即查看]         │
│  [了解更多 ↓]          │
│                       │
│  ★ 已追蹤 2,000+ 支    │
└───────────────────────┘
```

- 標題字級：`1.75rem`（28px）
- 副標題字級：`1rem`（16px）
- CTA 按鈕：全寬（width: 100%）
- 社會證明：簡化為一行

### 3.3 Features Section 詳細設計

#### Desktop — 三欄卡片

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│              │  │              │  │              │
│    📅        │  │    🔍        │  │    ♡         │
│              │  │              │  │              │
│  配息行事曆   │  │  即時搜尋     │  │  追蹤清單     │
│              │  │              │  │              │
│  一目了然     │  │  快速找到     │  │  跨裝置同步   │
│  配息日期     │  │  你關注的     │  │  隨時掌握     │
│              │  │  股票配息     │  │  投資動態     │
└──────────────┘  └──────────────┘  └──────────────┘
```

- 卡片：背景 `--surface`，border-radius 16px，padding 32px
- 圖示：48×48px，背景 `--dividend-bg`，border-radius 12px
- 標題：`1.125rem`（18px），font-weight 600
- 描述：`0.9375rem`（15px），color `--text-secondary`
- 間距：卡片之間 24px
- Hover：`transform: translateY(-4px)` + `box-shadow`

#### Mobile — 單欄堆疊

```
┌───────────────────────┐
│  📅  配息行事曆        │
│  一目了然配息日期       │
├───────────────────────┤
│  🔍  即時搜尋          │
│  快速找到你關注的       │
├───────────────────────┤
│  ♡  追蹤清單           │
│  跨裝置同步隨時掌握     │
└───────────────────────┘
```

- 卡片改為橫向排列（icon 在左，文字在右）
- 間距：16px

### 3.4 How It Works Section

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                    使用方式超簡單                              │
│                                                              │
│     ① 搜尋股票        ② 加入追蹤        ③ 掌握時程           │
│     ─────────────     ─────────────     ─────────────        │
│     輸入代號或名稱     點擊愛心加入       行事曆自動標示        │
│     快速找到標的       追蹤清單           配息日期              │
│                                                              │
│     ←────────────── 步驟流程 ──────────────→                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 使用步驟圓圈：64×64px，背景 `--tab-active-bg`，color white
- 步驟之間：箭頭連接線（SVG）
- 標題：`1.5rem`（24px），font-weight 700

### 3.5 CTA Section

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│              準備好掌握你的配息了嗎？                           │
│                                                              │
│              [📅 開始使用 StockPayDay]                        │
│                                                              │
│              免費使用 · 無需註冊 · 資料每日更新                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

- 背景：`--surface` 或漸層（light: `#f0f7ff` → `#ffffff`）
- CTA：大按鈕，height 56px，font-size 1.125rem
- 補充文字：`0.875rem`，color `--text-muted`

### 3.6 Footer 設計

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  StockPayDay++                                               │
│  提醒投資人股利發放日期的工具。                                 │
│                                                              │
│  [功能] [GitHub] [聯絡我們]                                   │
│                                                              │
│  © 2026 StockPayDay++ · MIT License                          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. 狀態矩陣

### 4.1 Primary CTA 按鈕

| 狀態 | 背景 | 文字 | Box Shadow | 動畫 |
|------|------|------|------------|------|
| **Idle** | `--tab-active-bg` (#1a73e8) | white | none | — |
| **Hover** | `--tab-active-bg`  darken 10% | white | `0 4px 12px rgba(26,115,232,0.3)` | `all 0.2s ease` |
| **Focus** | `--tab-active-bg` | white | `0 0 0 3px rgba(26,115,232,0.4)` | — |
| **Active** | `--tab-active-bg` darken 15% | white | none | — |
| **Disabled** | `--surface-2` | `--text-muted` @ 50% | none | — |

### 4.2 Secondary CTA 按鈕

| 狀態 | 背景 | 文字 | Border | 動畫 |
|------|------|------|--------|------|
| **Idle** | transparent | `--text-secondary` | 1px solid `--border` | — |
| **Hover** | `--surface-2` | `--text` | 1px solid `--border` | `all 0.2s ease` |
| **Focus** | transparent | `--text` | 1px solid `--border` | `box-shadow: 0 0 0 3px var(--focus-ring)` |

### 4.3 Feature Card

| 狀態 | 背景 | Border | Transform | Box Shadow |
|------|------|--------|-----------|------------|
| **Idle** | `--surface` | 1px solid `--border` | none | none |
| **Hover** | `--surface` | 1px solid `--border` | `translateY(-4px)` | `0 8px 24px rgba(0,0,0,0.08)` |
| **Focus** | `--surface` | 1px solid `--tab-active-bg` | none | `0 0 0 3px var(--focus-ring)` |

---

## 5. Design Token 表

### 5.1 新增 Token

| Token | Light Value | Dark Value | 說明 |
|-------|-------------|------------|------|
| `--hero-bg` | `#f0f7ff` | `#0f172a` | Hero Section 背景 |
| `--hero-gradient` | `linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%)` | `linear-gradient(135deg, #0f172a 0%, #111827 100%)` | Hero 漸層 |
| `--feature-icon-bg` | `rgba(26,115,232,0.1)` | `rgba(96,165,250,0.15)` | Feature 圖示背景 |
| `--feature-icon-color` | `#1a73e8` | `#60a5fa` | Feature 圖示顏色 |
| `--step-circle-bg` | `#1a73e8` | `#60a5fa` | 步驟圓圈背景 |
| `--cta-section-bg` | `#f9fafb` | `#1f2937` | CTA Section 背景 |
| `--footer-bg` | `#ffffff` | `#111827` | Footer 背景 |
| `--card-radius` | `16px` | `16px` | 卡片圓角 |
| `--section-padding` | `80px 0` | `80px 0` | Section 上下內距 |
| `--section-padding-mobile` | `48px 0` | `48px 0` | Mobile Section 內距 |

### 5.2 字級系統

| 用途 | Desktop | Mobile | Font Weight |
|------|---------|--------|-------------|
| Hero 標題 | `2.5rem` (40px) | `1.75rem` (28px) | 700 |
| Hero 副標題 | `1.25rem` (20px) | `1rem` (16px) | 400 |
| Section 標題 | `1.5rem` (24px) | `1.25rem` (20px) | 700 |
| Feature 標題 | `1.125rem` (18px) | `1rem` (16px) | 600 |
| Feature 描述 | `0.9375rem` (15px) | `0.875rem` (14px) | 400 |
| CTA 按鈕文字 | `1rem` (16px) | `1rem` (16px) | 600 |
| 補充文字 | `0.875rem` (14px) | `0.8125rem` (13px) | 400 |

### 5.3 間距系統

| 用途 | Desktop | Mobile |
|------|---------|--------|
| Section 上下內距 | 80px | 48px |
| Section 左右內距 | 24px | 16px |
| 卡片之間 | 24px | 16px |
| 卡片內距 | 32px | 24px |
| 元件之間（小） | 8px | 8px |
| 元件之間（中） | 16px | 12px |
| 元件之間（大） | 24px | 16px |

---

## 6. RWD 行為表

| 斷點 | Hero 標題 | Hero 副標題 | CTA 按鈕 | Features | How It Works | CTA Section |
|------|-----------|-------------|----------|----------|--------------|-------------|
| **≥ 1024px** | 40px, max-width 600px | 20px | 兩顆並排 (primary + secondary) | 三欄卡片 | 步驟橫排 + 箭頭 | 全寬，大按鈕 |
| **768–1023px** | 32px | 18px | 兩顆並排 | 三欄卡片（縮小） | 步驟橫排 | 全寬 |
| **≤ 767px** | 28px | 16px | 單欄堆疊（全寬） | 單欄橫向卡片 | 步驟縱排 | 全寬，全寬按鈕 |

### 6.1 Mobile 特殊處理

- Hero 圖示（如有）：隱藏或縮為 64×64 icon
- CTA 按鈕：width 100%，改為 column 排列
- Features：改為横排卡片（icon 左 + 文字右）
- How It Works：步驟縱排，箭頭改為向下
- Footer：連結改為縱排

---

## 7. 無障礙清單（WCAG 2.1 AA）

| WCAG SC | 要求 | 實作方式 |
|---------|------|----------|
| **1.4.3** Contrast (Minimum) | 文字對比 ≥ 4.5:1（一般文字）| Hero 標題 `--text` on `--hero-bg` ≈ 12:1；副標題 `--text-secondary` on `--hero-bg` ≈ 7:1 |
| **1.4.11** Non-text Contrast | UI 元件對比 ≥ 3:1 | CTA 按鈕 background vs hero-bg ≈ 4.5:1；feature card border vs bg ≈ 3:1 |
| **2.4.7** Focus Visible | 鍵盤使用者可見 focus indicator | 所有 CTA + card 使用 `box-shadow: 0 0 0 3px var(--focus-ring)` |
| **2.5.5** Target Size | 觸控目標 ≥ 44×44px | CTA 按鈕 height 48px（desktop）/ 44px（mobile）|
| **4.1.2** Name, Role, Value | 自訂元件有正確 ARIA | CTA 按鈕使用 `<a>` 或 `<button>` + `aria-label` |

### 7.1 鍵盤遷移順序

```
Header → Hero CTA (Primary) → Hero CTA (Secondary) → Feature Card 1 → Feature Card 2 → Feature Card 3 → How It Works (無互動) → Bottom CTA → Footer Links
```

---

## 8. 實作建議

### 8.1 路由調整

```typescript
// router/index.ts
{
  path: '/',
  name: 'landing',
  component: LandingView,  // 改為 LandingView
},
{
  path: '/app',
  name: 'home',
  component: HomeView,     // 行事曆移到 /app
},
```

### 8.2 LandingView 結構建議

```vue
<template>
  <div class="landing">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>你的股利，不再錯過。</h1>
        <p>StockPayDay 幫你掌握每一筆配息時程。</p>
        <div class="hero-actions">
          <a href="#/app" class="btn-primary">📅 立即查看配息行事曆</a>
          <a href="#features" class="btn-secondary">了解更多 ↓</a>
        </div>
        <p class="social-proof">★ 已追蹤超過 2,000 支股票的配息時程</p>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="features">
      <h2>為什麼選擇 StockPayDay</h2>
      <div class="features-grid">
        <div class="feature-card">...</div>
        <div class="feature-card">...</div>
        <div class="feature-card">...</div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="how-it-works">
      <h2>使用方式超簡單</h2>
      <div class="steps">...</div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <h2>準備好掌握了嗎？</h2>
      <a href="#/app" class="btn-primary btn-large">📅 開始使用 StockPayDay</a>
      <p>免費使用 · 無需註冊 · 資料每日更新</p>
    </section>

    <!-- Footer -->
    <footer>...</footer>
  </div>
</template>
```

### 8.3 CSS 重點調整

```css
/* Hero Section */
.hero {
  background: var(--hero-gradient);
  padding: var(--section-padding);
  text-align: center;
}

.hero h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 1rem;
}

@media (max-width: 767px) {
  .hero h1 { font-size: 1.75rem; }
}

/* Feature Cards */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

@media (max-width: 767px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  .feature-card {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  padding: 32px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* CTA Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  padding: 0 32px;
  background: var(--tab-active-bg);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-primary:hover {
  box-shadow: 0 4px 12px rgba(26, 115, 232, 0.3);
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  padding: 0 32px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}
```

---

## 9. 驗收清單

### 9.1 視覺

- [ ] Hero Section 背景使用漸層（`--hero-gradient`）
- [ ] Hero 標題字級：Desktop 40px / Mobile 28px
- [ ] Feature Cards 三欄（Desktop）/ 單欄横排（Mobile）
- [ ] CTA 按鈕高度 ≥ 44px
- [ ] 所有色彩使用 CSS 變數（無硬編碼色值）
- [ ] 深色模式完整適配

### 9.2 互動

- [ ] Primary CTA hover 有 box-shadow 效果
- [ ] Feature Card hover 有 translateY + shadow 效果
- [ ] 所有 CTA focus 時顯示 focus ring
- [ ] 錨點連結（#features）平滑滾動

### 9.3 無障礙

- [ ] 所有 CTA 使用 `<a>` 或 `<button>`（非 div+@click）
- [ ] 文字對比 ≥ 4.5:1
- [ ] 觸控目標 ≥ 44×44px
- [ ] 鍵盤 Tab 遷移順序正確

### 9.4 RWD

- [ ] Desktop (≥ 1024px)：完整三欄 Features
- [ ] Tablet (768–1023px)：三欄 Features（縮小）
- [ ] Mobile (≤ 767px)：單欄 Features + 全寬 CTA

### 9.5 路由

- [ ] `/` 指向 LandingView（新首頁）
- [ ] `/app` 指向 HomeView（行事曆）
- [ ] Header Logo 點擊回到 `/`
- [ ] CTA 按鈕導航至 `/#/app`

---

## 附錄：設計決策紀錄

| 決策 | 理由 | 替代方案 |
|------|------|----------|
| Hero 使用文字為主（無大圖） | 靜態站部署，避免大圖載入延遲；文字更直接 | 使用插圖/截圖（需額外資源） |
| Features 使用三欄卡片 | 資訊密度適中，視覺平衡 | 使用 horizontal scroll（mobile 可考慮） |
| CTA 按鈕使用 border-radius 12px | 現代感，與既有 6px / 8px 圓角系統一致 | 使用 pill shape（border-radius 999px） |
| Social Proof 使用文字數據 | 零額外依賴，靜態站可手動更新 | 使用第三方評價 widget（增加複雜度） |
| 路由改為 `/` = Landing, `/app` = App | 符合商業產品慣例（首頁 → 應用） | 保留現有路由（但首頁無意義） |
