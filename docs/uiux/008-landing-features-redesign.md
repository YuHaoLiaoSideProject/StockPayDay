# 008 — Landing Features 區塊重新設計（或移除）

> **範圍**：`/` 首頁（LandingView）中的 `#features` 區塊  
> **文件類型**：決策分析 + 比較稿  
> **日期**：2026-08-24

---

## 1. 現況審計

### 1.1 架構現狀

| 項目 | 現狀 |
|------|------|
| 路由 | 無獨立 `/features` 路由；`#features` 為 LandingView 內的錨點區塊 |
| 結構 | Hero → **Features（3卡片）** → How It Works → CTA → Footer |
| Features 內容 | 3 張卡片：配息行事曆、即時搜尋、追蹤清單 |
| CSS 樣式 | `.features` 區塊：`padding: var(--section-padding) 24px`（80px） |
| RWD | Mobile ≤767px 時 3 卡片改為橫向單列（icon + 文字水平排列） |

### 1.2 審計表

| # | 問題 | 嚴重度 | 位置 |
|---|------|--------|------|
| 1 | 與 Hero 區塊高度重疊 — Hero 已說明「掌握配息時程」，Features 再以不同措辭重複 | P2 | `LandingView.vue` 第 42–85 行 |
| 2 | 與 How It Works 重疊 — How It Works 已展示「搜尋 → 追蹤 → 掌握」3步，Features 再拆開強調 | P2 | `LandingView.vue` 第 87–118 行 |
| 3 | Feature Card 為通用行銷文案，無實際畫面截圖或數據佐證 | P2 | `style.css` `.feature-card` |
| 4 | 增加 CTA 前的滾動距離 ~320px（padding 160px + 卡片高度 ~160px） | P3 | `style.css` `.features` |
| 5 | 無互動元素 — 純靜態展示，無法點擊體驗功能 | P3 | `LandingView.vue` |

### 1.3 宣稱驗證

- **「3 卡片在同一列」**：Desktop ≥1024px 時 `grid-template-columns: repeat(3, 1fr)` 確認單列；Mobile ≤767px 改為 `1fr` 單欄 ✓
- **「Feature Card 有 hover 效果」**：`transform: translateY(-4px)` + `box-shadow` ✓（但無點擊行為）

---

## 2. 決策分析

### 2.1 為什麼 Utility App 不需要 Feature List

| 論點 | 說明 |
|------|------|
| **用戶行為** | Utility app 用戶「直接用」而非「讀功能列表後再決定」 |
| **資訊冗餘** | Hero（價值主張）+ How It Works（操作流程）已完整覆蓋 |
| **轉換漏斗** | Landing page 每多一屏，跳出率增加 10–20%（industry benchmark） |
| **Mobile 優先** | 本 app 為 Mobile-first，用戶在手機上不會閱讀長篇功能介紹 |

### 2.2 決策：移除 Features 區塊

**理由：**
1. Hero 的 `h1` + `subtitle` + `social-proof` 已足夠傳達價值
2. How It Works 的 3 步流程已展示核心操作
3. CTA 按鈕「立即查看配息行事曆」直接引導用戶進入 app
4. 移除後 landing page 從 5 段縮減為 4 段，減少 ~20% 滾動距離

**不保留的替代方案：**
- ❌ 「精簡為 1 張卡片」— 仍然冗餘
- ❌ 「改為 app 畫面截圖」— 截圖維護成本高，且 app 畫面已在 How It Works 後的 CTA 引導用戶自行體驗
- ❌ 「加上數據（如「追蹤 2000+ 支股票」）」— 已在 Hero 的 `social-proof` 中

### 2.3 目標結構

**BEFORE（現狀）：**
```
Hero → Features（3卡片）→ How It Works → CTA → Footer
```

**AFTER（建議）：**
```
Hero → How It Works → CTA → Footer
```

---

## 3. 設計原則

1. **資訊密度優先** — 每個區塊必須傳達獨特價值，不重複
2. **行動導向** — Landing page 的唯一目標是引導用戶進入 app
3. **最少滾動** — 減少 CTA 前的滾動距離，提高轉換率
4. **Mobile-first** — 在手機上，每一屏都很珍貴

---

## 4. 驗收清單

- [ ] Features 區塊（`.features` section）已從 `LandingView.vue` 移除
- [ ] Hero → How It Works → CTA → Footer 的流暢度不受影響
- [ ] `#features` 錨點連結已從 footer 移除或改為 `#`（無目標）
- [ ] Mobile RWD 響應正常
- [ ] Dark mode 正常
- [ ] 無 console error
- [ ] CSS 中 `.features` 相關樣式可保留（供未來使用）或清理

---

## 5. 檔案清單

| 檔案 | 說明 |
|------|------|
| `docs/uiux/008-landing-features-redesign.md` | 本文件 |
| `docs/uiux/008-landing-features-redesign-mockup.html` | BEFORE / AFTER 比較稿 |
