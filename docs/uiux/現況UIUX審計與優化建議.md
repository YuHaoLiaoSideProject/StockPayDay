# StockPayDay++ 現況 UI/UX 審計與優化建議

> 審計日期：2025-08-22 ｜ 方法：程式碼走查 + Playwright 實測（desktop 1280×900 / mobile 375×812，light/dark 雙主題）
> 實測環境：`npm run dev`（vite 5.4.21），全程 console error = 0

## 一、審計範圍

| 畫面 | 路由 | 元件 |
|---|---|---|
| 首頁（行事曆／列表） | `/#/` | App.vue、ViewSwitcher、Calendar、CalendarDay、ListView、ListItem、DayDetail（Modal） |
| 單股頁 | `/#/stock/:code` | StockView、StockDetail、WatchlistButton |
| 追蹤清單頁 | `/#/watchlist` | WatchlistView（page）、WatchlistView（component）、WatchlistEmpty |

## 二、審計發現（依嚴重度）

### P1 — 阻礙使用／明顯缺陷

| # | 問題 | 證據 | 位置 |
|---|---|---|---|
| 1 | **Mobile（375px）Header 元件重疊**：搜尋框壓在 logo 上、追蹤清單按鈕疊在搜尋框上 | logo x=16 w=144（16–160）；search-bar x=120 w=200（120–320）；watchlink x=172 w=94（172–266）；header scrollWidth=375 無捲軸，直接互相覆蓋 | `App.vue` / `.app-header` CSS |
| 2 | **可點擊元素無鍵盤存取**（WCAG 2.1.1）：`.calendar-day`、`.list-item`、`.modal-list li` 都是 div+@click，無 tabindex／role；鍵盤使用者完全無法操作行事曆與列表 | 程式碼走查 | `CalendarDay.vue`、`ListItem.vue`、`DayDetail.vue` |
| 3 | **單股頁出現兩個「← 返回」按鈕**：StockView 的 `.stock-top-bar` 已有一個返回鈕，StockDetail 內又再放一個，重複且浪費版面 | 實測：`"← 返回"` ×2（innerText 確認） | `StockView.vue`、`StockDetail.vue` |
| 4 | **Mobile Header 擁擠**：logo 文字被搜尋框遮住只剩「StockPayD」，品牌識別受損 | mobile 截圖 | `App.vue` |

### P2 — 體驗／一致性问题

| # |問題 | 證據 | 位置 |
|---|---|---|---|
| 5 | **觸控目標過小**（<44px）：theme-toggle 31×31、view-switcher 按鈕高 34、watchlist-btn--sm 24×24、clear-btn ≈23×23 | Playwright 量測 | `style.css`、`SearchBar.vue` |
| 6 | **行事曆列高不均**：無配息日格高 48px；有配息日因 label 最多 4 行（3 支＋＋N），格高長到 ~100px，整體格線凌亂 | Playwright 量測＋截圖 | `CalendarDay.vue` |
| 7 | **配息代號字級過小**：`.dividend-label` 10px、`.dividend-more` 9px，難以閱讀 | CSS 走查 | `style.css` |
| 8 | **List view 未分組、無 sticky header、無虛擬捲動**：200+ 筆資料全部平鋪渲染，日期每行重複顯示（如 2026-08-25 ×5 行連續），掃讀困難；且金額為 `$0.00` 的項目照樣顯示 | 截圖＋實測（listItemH=60、rows≈200） | `ListView.vue` |
| 9 | **Watchlist 行事曆點日期無反應**：`handleDateClick()` 故意留空（註解自述 intentional empty），但格子有 `cursor:pointer`＋hover 樣式 → 死區（dead affordance） | 程式碼走查 | `components/WatchlistView.vue` |
| 10 | **Modal 不符合 ARIA dialog**：無 `role="dialog"`／`aria-modal`、focus 只移到容器但無 focus trap（Tab 可跑到背景）、背景可捱動、日期顯示 raw ISO 格式「2026-08-21 配息股票」 | 程式碼走查 | `DayDetail.vue` |
| 11 | **對比不足（WCAG 1.4.11）**：`--text-muted: #9ca3af` 對白底對比 ≈2.5:1（<4.5:1），用於 weekday、empty/error msg、subtitle、list-header 等 | CSS 計算 | `style.css` |
| 12 | **Desktop 版面未利用寬度**：內容固定 480px／main 672px 兩種寬度並存不一致；1280px 下兩側大量留白、行事曆偏小 | 量測：content 480／main 672 | `HomeView`、`app-main` |

### P3 — 一致性／維護性

| # | 問題 | 位置 |
|---|---|---|
| 13 | **BackButton.vue 元件已寫但未使用**：StockView 自行寫 `<button class="back-button">`，元件化不一致 | `BackButton.vue`、`StockView.vue` |
| 14 | **Emoji 當圖示**（跨平台渲染不一致）：header ❤️、ViewSwitcher 📅📋、WatchlistEmpty 📋🔍📅、標題 ❤️；與既有 inline SVG 圖示（logo、search、theme、heart）混用 | `App.vue`、`ViewSwitcher.vue`、`WatchlistEmpty.vue` |
| 15 | **Reduced-motion 未涵蓋 spinner**：`prefers-reduced-motion` 區塊只取消 transition／transform，`.spinner { animation: spin }` 未停用 | `style.css` |
| 16 | **Blur+setTimeout(150ms) hack**：下拉關閉靠 blur timer，屬脆弱模式（建議 focusout+relatedTarget 或 pointerdown） | `SearchBar.vue` |
| 17 | **RWD 隱藏欄位 hard-code**：`.history-table td:nth-child(2)` 隱藏除權息日，結構脆弱（應用 class 控制） | `style.css` |
| 18 | **Dark mode 掛在 `.app-root`**：非 html/body 層級，html 背景仍透明，overscroll 可能露白（實測 body 有跟著變色，但架構依賴 body var(--bg) 繼承鏈） | `App.vue`、`useDarkMode.ts` |

## 三、優化建議（對應 P1/P2）

### A. Header／RWD（P1-1、P1-4、P2-12）
1. Mobile（<768px）：搜尋改為 icon，點擊展開全寬搜尋列（或第二列）；追蹤清單改 icon＋badge。
2. Desktop（≥1024px）：內容上限統一（建議 main 與 content 同用 720–800px 或 grid 兩欄），消除 480/672 並存。**行事曆桌面版加寬至約 560px（流式寬度 width:100% + max-width:560px，≤767px 收窄至容器全寬）**。

### B. 可及性（P1-2、P2-10、12）
3. 行動曆格子／列表列／modal 列改 `<button>` 或加 `role="button"`＋`tabindex="0"`＋Enter/Space 鍵盤處理。
4. Modal 加 `role="dialog"`、`aria-modal="true"`、aria-labelledby，並做簡易 focus trap（Tab 循環於 modal 內）＋背景 `inert`／`overflow:hidden`。
5. `--text-muted` 改深（如 #6b7280 ≈4.7:1）或僅用於 ≥18.66px 大字。

### C. 行事曆／列表資訊設計（P2-6、7、8、9）
6. 格子高度統一（min-height 48px＋max-height 64px，超過 2 支縮為「＋N」），label 字級提升至 11–12px。
7. List view：依日期分組（sticky date header）＋虛擬捲動（vue-virtual-scroller）；金額為 0 時隱藏金額欄或顯示「—」。
8. Watchlist 點日期 → 打開 DayDetail modal（與首頁行為一致），或移除 pointer/hover 樣式。

### D. 觸控／互動（P2-5、P3-15、16）
9. 所有可點擊目標 ≥44×44px（mobile）；theme-toggle、clear-btn、watchlist-btn--sm 至少加大 padding 至 40–44。
10. Spinner 加入 `@media (prefers-reduced-motion: reduce){ .spinner{ animation: none } }`。
11. 下拉關閉改 `focusout`＋`relatedTarget.contains` 檢查。

### E. 一致性／元件化（P3-13、14）
12. 統一使用 `BackButton.vue`（StockView 移除自寫返回鈕）。
13. Emoji 全部換成 inline SVG（heart、calendar、list、magnifier、clipboard），並集中為 `Icon.vue`。

## 四、驗收清單（修復後必測）

- [ ] 375px：header 無重疊（元素 bounding box 交集 = 0）
- [ ] 全站可點擊元素皆可用 Tab 到達＋Enter/Space 觸發
- [ ] 觸控目標皆 ≥44×44（mobile）
- [ ] 行事曆列高一致；label ≥11px
- [ ] List：分組＋sticky header；無 $0.00 裸顯
- [ ] Modal：ARIA role/trap/背景鎖定；日期本地化格式（如「8月21日」）
- [ ] 對比 ≥4.5:1（一般文字）
- [ ] reduced-motion：spinner 停止轉動
- [ ] console error = 0（desktop＋mobile、light＋dark）

## 五、實測數據附錄

```json
{
 "measure-desktop": {"themeToggle":{"h":31,"w":31},"watchlistLink":{"h":34,"w":94},"searchInput":{"h":36,"w":256},"viewSwitcherBtn":{"h":34,"w":87},"calendarDayH":48,"contentWidth":480,"mainWidth":672,"headerH":61},
 "measure-mobile": {"themeToggle":{"h":31,"w":31},"watchlistLink":{"x":172,"w":94},"searchInput":{"x":120,"w":200},"logo":{"x":16,"w":144},"calendarDayH":48,"contentWidth":343,"headerH":61},
 "overlap-check-mobile": {"logo":"16–160","search":"120–320","watchlink":"172–266","結論":"三段互相重疊"},
 "darkcheck": {"bodyBg":"rgb(17,24,39)","htmlBg":"rgba(0,0,0,0)"},
 "stock-page": {"backButtons":2,"tableRows":1},
 "consoleErrors": 0
}
```
