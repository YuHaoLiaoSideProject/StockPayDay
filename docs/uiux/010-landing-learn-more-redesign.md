# 010 — Landing「了解更多」流程重設計

> **範圍**：`/` 首頁（LandingView）的「了解更多 ↓」按鈕 + How It Works 區塊  
> **文件類型**：問題分析 + 目標設計  
> **日期**：2026-08-25  
> **關聯**：008（Features 移除）、009（L-2、C1）

---

## 1. 現況審計

### 1.1 問題定位

| 項目 | 現狀 |
|------|------|
| 按鈕 | `<a href="#how-it-works" class="landing-btn landing-btn-secondary">了解更多 ↓</a>` |
| 目標區塊 | `<section id="how-it-works" class="how-it-works">`（同頁錨點） |
| 路由模式 | `createWebHashHistory`（`/#/` 前綴） |

### 1.2 根因分析

Vue Router hash mode 將 `window.location.hash` 作為路由路徑：

```
使用者點擊 → href="#how-it-works"
           → URL 變為 /#/how-it-works（Vue Router 解釋為路由 /how-it-works）
           → 路由表中無 /how-it-works → 空白頁
```

**正確行為應為**：滾動至同頁 `#how-it-works` 區塊（錨點跳轉）。

### 1.3 審計表

| # | 問題 | 嚴重度 | 位置 |
|---|------|--------|------|
| 1 | **「了解更多 ↓」進入空白頁** — hash mode 下錨點被路由攔截 | **P1** | `LandingView.vue:34` |
| 2 | How It Works 區塊僅有 3 個文字步驟，無視覺輔助 | P2 | `LandingView.vue:97-118` |
| 3 | Footer 的「功能介紹」連結（`href="#how-it-works"`）同樣有空白頁問題 | P2 | `LandingView.vue:133` |
| 4 | CTA 按鈕與「了解更多」之間缺少視覺層次引導 | P3 | `LandingView.vue:31-36` |

---

## 2. 設計原則

1. **修復 P1 bug** — 錨點滾動必須正常運作
2. **漸進式揭露** — How It Works 用視覺化步驟降低認知負擔
3. **行動導向** — 每個區塊最終引導至 CTA
4. **Mobile-first** — 手機上每屏資訊密度最大化

---

## 3. 目標設計

### 3.1 修復錨點滾動

**方案 A（推薦）：`@click.prevent` + `scrollIntoView`**

```vue
<a href="#how-it-works"
   class="landing-btn landing-btn-secondary"
   @click.prevent="scrollToSection('how-it-works')">
  了解更多 ↓
</a>
```

```ts
function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}
```

**優點**：
- 繞過 Vue Router 的 hash 解釋
- 原生 `scrollIntoView` 支援 smooth scrolling
- 錨點 URL 仍可分享（`/#/?section=how-it-works` 或保持 `#how-it-works`）

**方案 B：改用 `router-link` + `@click`**

不推薦 — 需要新增路由或使用 `router.push` + `$nextTick` + `scrollIntoView`，複雜度高。

### 3.2 How It Works 區塊重新設計

**現狀**：3 個圓形數字 + 標題 + 描述，水平排列，無實際畫面。

**目標**：加入 app 畫面截圖 / 插圖，強化「一看就懂」的視覺引導。

#### 設計方案

```
┌─────────────────────────────────────────────────┐
│            使用方式超簡單                         │
│      三個步驟，開始掌握你的配息                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 🔍 搜尋   │→ │ ❤️ 追蹤   │→ │ 📅 掌握   │      │
│  │          │  │          │  │          │      │
│  │ [搜尋框]  │  │ [愛心動畫]│  │ [行事曆]  │      │
│  │ 2330     │  │ 2330 ♥   │  │ 8月25日   │      │
│  │ 台積電    │  │ 台積電    │  │ ●4支配息  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                  │
│  輸入代號或名稱    點擊愛心加入     行事曆自動標示   │
│  快速找到標的      你的追蹤清單     配息日期         │
│                                                  │
├─────────────────────────────────────────────────┤
│          [立即查看配息行事曆]  ← CTA              │
│          免費使用 · 無需註冊                       │
└─────────────────────────────────────────────────┘
```

#### 元件規格

| 元件 | 說明 |
|------|------|
| Step Card | 白色卡片（`var(--surface)`），圓角 12px，hover 時 `translateY(-2px)` |
| Step Visual | 每步下方有一個 mini 畫面（純 CSS 模擬 app 畫面），非截圖 |
| Step Number | 藍色圓形（`var(--step-circle-bg)`），56×56px |
| Step Arrow | 步驟間的 → 箭頭（mobile 改為 ↓） |
| Step Text | 標題 1rem/600 + 描述 0.875rem/`var(--text-secondary)` |

### 3.3 CTA 區塊優化

**現狀**：獨立 section，與 How It Works 分離。

**目標**：將 CTA 整合進 How It Works 底部，減少一次 scroll。

```
How It Works（3步驟）
    ↓
CTA 按鈕 + 免費使用提示
    ↓
Footer
```

---

## 4. 狀態矩陣

| 狀態 | 視覺 | 互動 |
|------|------|------|
| Default | 3 張步驟卡片水平排列 | — |
| Hover（Desktop）| 卡片微上浮 + 陰影 | — |
| Hover（CTA）| 按鈕陰影加深 + 上浮 | — |
| Mobile | 卡片縱向排列，箭頭旋轉 90° | — |
| Dark Mode | 卡片背景 `var(--surface)`，文字 `var(--text)` | — |
| Reduced Motion | 無動畫 | — |

---

## 5. RWD 行為

| 斷點 | 佈局 | CTA |
|------|------|-----|
| ≥1024px | 3 卡片水平 + 箭頭 | 位於 How It Works 底部 |
| 768–1023px | 3 卡片水平（縮小間距）| 位於 How It Works 底部 |
| ≤767px | 3 卡片縱向 + 箭頭旋轉 | 全寬按鈕 |

---

## 6. 無障礙清單

| WCAG | 要求 | 實作 |
|------|------|------|
| 1.3.1 | 語意結構 | 每步用 `<div role="group" aria-label="步驟 N">` |
| 2.4.1 | 跳過區塊 | 錨點滾動後 focus 留在目標區塊 |
| 2.4.7 | Focus ring | CTA 按鈕有 `:focus-visible` box-shadow |
| 4.1.2 | 名稱/角色 | 步驟卡片無互動元素，不需額外 ARIA |

---

## 7. 實作建議

### 7.1 修改 `LandingView.vue`

1. **新增 `scrollToSection` function**
2. **替換所有 `href="#how-it-works"` 為 `@click.prevent="scrollToSection('how-it-works')"`
3. **How It Works 區塊加入 mini 畫面視覺**
4. **CTA 按鈕移至 How It Works 底部**（或保持獨立 section 但縮短間距）

### 7.2 CSS 調整

1. `.step` 加入 `background: var(--surface); border-radius: 12px; padding: 1.5rem`
2. `.step-visual` 新增 mini 畫面樣式（純 CSS）
3. `.how-it-works` 的 `padding-bottom` 加入 CTA 空間

---

## 8. 驗收清單

- [ ] 點擊「了解更多 ↓」平滑滾動至 How It Works 區塊（非空白頁）
- [ ] Footer「功能介紹」連結同樣正常滾動
- [ ] How It Works 3 步驟有 mini 畫面視覺輔助
- [ ] CTA 按鈕在 How It Works 底部可見
- [ ] Mobile 縱向排列正常
- [ ] Dark mode 色彩正確
- [ ] 無 console error
- [ ] `prefers-reduced-motion` 時無動畫

---

## 9. 檔案清單

| 檔案 | 說明 |
|------|------|
| `docs/uiux/010-landing-learn-more-redesign.md` | 本文件 |
| `docs/uiux/010-landing-learn-more-redesign-mockup.html` | BEFORE / AFTER 比較稿 |
