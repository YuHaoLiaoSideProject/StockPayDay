# 跨裝置追蹤清單同步 — 測試計畫

> **對應 BDD**：`docs/bdds/phases/phase-9-跨裝置追蹤清單同步.feature`
> **操作流程**：`docs/interaction-flows/phases/phase-9-跨裝置追蹤清單同步.md`
> **開發規格**：`docs/development/phases/phase-9-跨裝置追蹤清單同步.md`（§8 測試覆蓋草案已依 BDD 補齊並整合於本章）
> **測試日期**：2026-08-23

---

## 1. 測試範圍總覽

本專案為**純前端靜態站（GitHub Pages），無後端**；同步依賴外部 kvdb.io（免登入雲端 JSON）。因此本測試計畫不含後端單元測試，由前端單元測試直接覆蓋同步引擎邏輯（merge／墓碑／退避／降級）。

| 層級 | 範圍 | 工具 | 負責 |
|------|------|------|------|
| 單元測試 | `useWatchlistSync`（merge 合併規則、pull/push、429 退避、輪詢生命週期） | Vitest + happy-dom | 前端 |
| 單元測試 | `useWatchlist`（add/remove 墓碑語意、舊資料遷移、localStorage 降級） | Vitest + happy-dom | 前端 |
| 單元測試 | `WatchlistSyncSettings`／匯出匯入 util（設定 UI 狀態顯示、匯出/匯入格式） | Vitest + Vue Test Utils | 前端 |
| 端對端測試 | 完整使用者操作流程（配對→跨裝置同步→停用→匯出/匯入備援） | Playwright（stub kvdb） | 前端 |
| 手動驗證 | 真實雙裝置 kvdb 同步、配對碼外流回收、真實隱私模式 | 手動 | QA |

**測試策略要點**（整合開發規格 §8）：

- ✅ **kvdb 模擬**：E2E 一律以 `page.route('https://kvdb.io/**')` 攔截（或本機測試伺服器）模擬 kvdb 的 GET 200/404、POST 200/429 行為，測試檔 `frontend/e2e/watchlist-sync.spec.ts`（見 §3.7 mock 策略）。
- ✅ **時鐘控制**：60 秒輪詢與 429 退避定時器使用 Playwright `page.clock` 快轉，避免真實等待（E2E）與 `vi.useFakeTimers()`（單元）。
- ✅ **符合 DoD**：未配對路徑零同步請求、既有 Phase 5a 測試全數通過為回歸基準。

---

## 2. 前端單元測試（Vitest）

> 執行：`cd frontend && npm run test:unit`
> 放置位置：`frontend/src/composables/__tests__/useWatchlistSync.spec.ts`、`frontend/src/composables/__tests__/useWatchlist.spec.ts`（擴充）、`frontend/src/components/__tests__/WatchlistSyncSettings.spec.ts`
> 案例 ID：`F-XX`（a/b/c 為 Scenario Outline 各列展開）

### 2.1 merge 合併規則（`useWatchlistSync`）

| # | 測試名稱 | Given | When | Then |
|---|---------|-------|------|------|
| F-04 | 合併為並集（Scenario 4） | 本地 items=[A]，雲端 items=[B] | 執行 merge(local, remote) | 結果同時含 A 與 B |
| F-11b | 墓碑為最終狀態（Scenario 11） | 雲端 items 含 `{code:X, deleted:true}`（較新 `updatedAt`），本地 items 含活躍的 X（較舊） | 執行 merge(local, remote) | 結果 X 維持 `deleted:true`，不被本地舊資料覆蓋 |
| F-12 | per-item last-write-wins（Scenario 12） | 本地 X `updatedAt=200`，雲端 X `updatedAt=100` | 執行 merge | X 採用本地（較新 `updatedAt`）一筆 |
| F-27b | 舊資料無 updatedAt 以 addedAt 比對（Scenario 27） | 雲端 X 僅有 `addedAt=300`（無 `updatedAt`），本地 X `addedAt=100`+`updatedAt=100` | 執行 merge | 以 `updatedAt ?? addedAt` 比對，雲端較新 → 採用雲端 |

### 2.2 useWatchlist 行為（remove 未配對／已配對、舊資料遷移）

| # | 測試名稱 | Given | When | Then |
|---|---------|-------|------|------|
| F-05 | 未配對 remove 與現況一致（Scenario 5） | 未設配對碼（`syncActive=false`），items 含 X | `remove('X')` | X 直接從 items 過濾移除（不寫墓碑），`isWatched('X')=false` |
| F-11a | 已配對 remove 寫墓碑（Scenario 11） | 已設配對碼（`syncActive=true`），items 含 X | `remove('X')` | X 保留於 items 但 `deleted:true`、`updatedAt` 更新；`isWatched('X')` 立即 false；`watchedCodes` 不含 X |
| F-27a | 舊資料載入遷移補 `updatedAt`（Scenario 27） | localStorage 存有舊格式 items（僅 `addedAt`，無 `updatedAt`／`deleted`） | 初始化 useWatchlist（讀取 localStorage） | 全部 item 補 `updatedAt = addedAt`（向後相容）；`isWatched`／排序等既有行為正常 |

### 2.3 useWatchlistSync 同步引擎（syncOnce／輪詢／退避）

> 以 `vi.stubGlobal('fetch', ...)` 模擬 kvdb 契約（200/404/429/網路錯誤）。

| # | 測試名稱 | Given | When | Then |
|---|---------|-------|------|------|
| F-03 | 首次配對上傳建立雲端清單（Scenario 3） | 已配對，本地 items=[A,B]，kvdb GET 回 404 | `syncOnce()` | 對雲端 POST 一筆含 A、B 的 doc；`status='synced'`；本地 items 不變 |
| F-08 | 本地變更 debounce 1.5s 後寫回（Scenario 8） | 已配對、`status='synced'`，fake timers | `add('X')` 後快轉 1.5 秒 | 觸發一次 `syncOnce`（fetch 被呼叫寫回）；未滿 1.5 秒前不觸發 |
| F-09 | 裝置 B 合併收到新增變更（Scenario 9） | 本地 items=[A]，kvdb GET 回雲端 items=[A,X] | `syncOnce()` | merge 後本地 items 含 X；`status='synced'` |
| F-10 | 前台每 60 秒自動檢查（Scenario 10） | 已配對、fake timers、`document.visibilityState='visible'` | 快轉 60 秒 | `syncOnce` 被呼叫（每 60s 一次） |
| F-13 | 立即同步（Scenario 13） | 已配對、`status='synced'` | 呼叫 `syncOnce()` | 狀態依序 `syncing` → `synced`；fetch 恰一次 |
| F-14 | 離線（非 429）失敗不影響本地（Scenario 14） | 已配對，fetch 丟出網路錯誤 | `add('X')` 後觸發 `syncOnce()` | `status='error'`、`lastError` 有值；本地 items 仍含 X（不受影響） |
| F-15 | 恢復連線自動合併離線變更（Scenario 15） | 上一次同步失敗、本地離線期間加入 X，fetch 恢復正常 | 模擬 `visibilitychange→visible` 觸發同步 | merge 成功、X 保留、`status='synced'`；不需重新 setToken |
| F-16 | 429 顯示退避訊息並自動恢復（Scenario 16） | 已配對，fetch 回 429 | 觸發 `syncOnce()`，快轉 30 秒，fetch 改回 200 | 期間 `status='error'`、`lastError='速率限制（429），30 秒後重試'`；退避結束自動重試單次成功 → `status='synced'`、退避歸零 |
| F-17a | 429 退避第 1 次 = 30 秒（Scenario 17 列 1） | 連續第 1 次遭遇 429 | 觸發 `syncOnce()` | 排程 30 秒後重試；`lastError` 含「30 秒」 |
| F-17b | 429 退避第 2 次 = 60 秒（Scenario 17 列 2） | 已連續 1 次 429 未成功 | 第 2 次遭遇 429 | 排程 60 秒後重試；`lastError` 含「60 秒」 |
| F-17c | 429 退避第 3 次 = 120 秒（Scenario 17 列 3） | 已連續 2 次 429 未成功 | 第 3 次遭遇 429 | 排程 120 秒後重試（上限）；`lastError` 含「120 秒」 |
| F-18 | 僅頁面可見時才同步（Scenario 18） | 已配對，`document.visibilityState='hidden'` | 快轉 120 秒（多個輪詢週期） | 不發送任何 fetch；切回 `visible` 時立即觸發一次同步 |
| F-19 | 停用同步後本地保留（Scenario 19） | 已配對、items 含 A | `clearToken()` | `status='disabled'`、輪詢停止（快轉 60s 無 fetch）、token 自 localStorage 移除、items 保留 |
| F-20 | 停用後重新啟用合併雲端（Scenario 20） | 已停用、本地保留 A，kvdb GET 回雲端 [A,B] | `setToken('new-token')` | `status='syncing'` 起跑 → 合併後 items 含 A、B → `status='synced'` |
| F-24 | 配對碼無效時失敗且本地不受影響（Scenario 24） | 已配對，kvdb GET 回 401 | `syncOnce()` | `status='error'`、`lastError` 有值；本地 items 不變；`setToken(correct)` 後恢復 |
| F-25 | 配對碼過期持續失敗（Scenario 25） | 已配對，kvdb 持續回 401 | 連續多次 `syncOnce()` | 每次均 `status='error'`；本地 items 不變；換新 token 後恢復 `synced` |
| F-26 | localStorage 失敗降級（Scenario 26） | `vi.stubGlobal('localStorage', { getItem/setItem 拋錯 })` | 初始化 useWatchlist 並 `add('A')` | 不拋例外、items 正常運作、`status='disabled'`（視同未配對）；同步引擎不啟動 |

### 2.4 WatchlistSyncSettings 元件（設定 UI 狀態顯示）

| # | 測試名稱 | Given | When | Then |
|---|---------|-------|------|------|
| F-01 | 啟動後記住配對碼並顯示同步中（Scenario 1） | 元件 mount，token 為空 | 輸入有效配對碼並 submit「啟動」 | `setToken` 被呼叫；token 寫入 `stockpayday-sync-token`；狀態列文字「同步中…」（mock fetch 延遲回應期間） |
| F-02 | 空輸入框無法啟動（Scenario 2） | token 輸入框為空 | 直接 submit「啟動」 | 不送出請求（`setToken` 不被呼叫）；狀態維持「未啟用同步」/未配對區塊 |
| F-06 | 未配對顯示設定區塊（Scenario 6） | 未配對（無 token） | mount 元件 | 顯示「🔄 跨裝置同步（選配）」標題與配對碼輸入框；含說明「不設定則完全不影響現有功能」 |
| F-07a | 狀態列顯示「同步中…」（Scenario 7 列 1） | mock `status='syncing'` | mount 元件（已配對分支） | 顯示文字「同步中…」，無上次同步時間 |
| F-07b | 狀態列顯示「已同步」+上次時間（Scenario 7 列 2） | mock `status='synced'`、`lastSyncedAt=固定時間` | mount 元件 | 顯示「已同步」並附 `上次同步 HH:MM:SS` |
| F-07c | 狀態列顯示「同步失敗」+錯誤訊息（Scenario 7 列 3） | mock `status='error'`、`lastError='同步失敗：連線錯誤'` | mount 元件 | 顯示「同步失敗」並附錯誤訊息 |

### 2.5 匯出／匯入備援 util

| # | 測試名稱 | Given | When | Then |
|---|---------|-------|------|------|
| F-21 | 匯出內容為目前追蹤項目（Scenario 21） | items 含活躍 X 與 `deleted:true` 的 Y | 執行匯出 | 匯出文字含 X（含 ETF／特別股），**不含**已移除的 Y |
| F-22 | 匯入合併且不重複（Scenario 22） | 本地已含 X；匯入內容含 X 與 Y | 執行匯入 | results 含 X、Y 各一筆（X 不重複加入） |
| F-23 | 匯入格式錯誤時清單不變（Scenario 23） | 本地含 X；匯入內容為非 JSON 或欄位錯誤 | 執行匯入 | 拋出/回傳格式錯誤；items 仍只有 X |

---

## 3. 端對端測試（Playwright）

> 測試檔：`frontend/e2e/watchlist-sync.spec.ts`
> 執行：`cd frontend && npm run test:e2e -- watchlist-sync.spec.ts`
> 案例 ID：`E2E-XX`（a/b/c 為 Scenario Outline 各列展開）；kvdb 一律以 `page.route` 攔截模擬（見 §3.7），部分情境使用 `page.clock` 快轉計時器。

| # | 測試名稱 | 操作步驟 | 預期結果 |
|---|---------|---------|---------|
| E2E-01 | 貼上配對碼啟用同步（Scenario 1） | 前往 /watchlist → 輸入有效配對碼 → 點「啟動」→ reload | 狀態列顯示「同步中…」；`localStorage['stockpayday-sync-token']` 已寫入；reload 後仍顯示已配對狀態列 |
| E2E-02 | 空配對碼無法啟動（Scenario 2） | 前往 /watchlist → 不輸入 → 點「啟動」 | 無任何 kvdb 請求（route 計數=0）；仍顯示未配對設定區塊 |
| E2E-03 | 首次配對上傳建立雲端清單（Scenario 3） | 先加入 2330 → 貼配對碼啟動（mock GET=404）→ 等同步完成 | kvdb 收到 POST 且 body 含 2330；狀態列「已同步」附上次同步時間；本機清單內容不變（仍恰一筆） |
| E2E-04 | 首次配對（雲端已有清單）合併並集（Scenario 4） | mock 雲端含 0056；本機已有 2330 → 貼配對碼啟動 | 同步後本機同時含 2330 與 0056；狀態列「已同步」 |
| E2E-05 | 未配對行為與現況一致且零請求（Scenario 5） | 不設配對碼 → 依序執行搜尋、加入、移除、切換行事曆/列表模式 | 所有操作與未同步版本一致；kvdb 請求計數維持 0 |
| E2E-06 | 未配對顯示同步設定區塊（Scenario 6） | 前往 /watchlist（未配對） | 顯示「🔄 跨裝置同步（選配）」區塊、配對碼輸入框與說明「不設定則完全不影響現有功能」 |
| E2E-07a | 狀態列：同步中…（Scenario 7 列 1） | mock fetch 延遲回應 → 貼配對碼啟動 | 狀態列顯示「同步中…」 |
| E2E-07b | 狀態列：已同步+時間（Scenario 7 列 2） | 貼配對碼並完成同步 | 狀態列顯示「已同步」並附「上次同步 HH:MM:SS」 |
| E2E-07c | 狀態列：同步失敗+錯誤訊息（Scenario 7 列 3） | mock fetch 回 500 → 貼配對碼啟動 | 狀態列顯示「同步失敗」並附錯誤訊息 |
| E2E-08 | 已配對新增自動寫回（Scenario 8） | 已配對 → 搜尋加入股票 X → `page.clock` 快轉 1.5s | ❤️ 立即變實心、徽章 +1；約 1.5s 後 kvdb 收到含 X 的 POST；狀態短暫「同步中…」後回「已同步」 |
| E2E-09 | 另一裝置切回即收到新增（Scenario 9） | 同 context 開 tab A/B（共用 token、mock 雲端共用）→ A 新增 X、等寫回 → B 切回 /watchlist | B 自動拉取合併，X 出現在 B 清單；兩 tab 內容一致 |
| E2E-10 | 前台每 60 秒自動檢查（Scenario 10） | tab B 停留前台 → mock 雲端被 tab A 更新為含 X → `page.clock` 快轉 60s | B 自動拉取並出現 X（無需切頁） |
| E2E-11 | 移除以墓碑傳播（Scenario 11） | tab A/B 同配對碼皆含 X → A 移除 X、等寫回 → B 切回 | A 立即移除 X；雲端收到含 `deleted:true` 墓碑的 POST；B 切回後 X 消失 |
| E2E-12 | 同股雙端最後寫入者勝出（Scenario 12） | mock 雲端含 X 移除墓碑（較早）；A 較晚加入 X 並寫回 → B 同步 | 合併後 X 保留於兩端清單（較新寫入者勝出） |
| E2E-13 | 立即同步（Scenario 13） | 已配對 → 點「立即同步」 | 狀態依序「同步中…」→「已同步」 |
| E2E-14 | 離線增刪正常且本地不受影響（Scenario 14） | mock fetch 全部回網路錯誤 → 加入 X | 本機清單正常更新；狀態列「同步失敗」附錯誤訊息；reload 後 X 仍在本機 |
| E2E-15 | 恢復連線自動合併（Scenario 15） | 承 E2E-14（離線加入 X）→ mock 恢復正常 → 切走再切回 /watchlist | 自動同步合併，X 保留且與雲端一致；狀態回「已同步」；不需重貼配對碼 |
| E2E-16 | 429 退避並自動恢復（Scenario 16） | mock GET/POST 回 429 → 觸發同步 → `page.clock` 快轉 30s → mock 回 200 | 狀態列顯示「速率限制（429），30 秒後重試」；退避期間本機增刪操作正常；退避結束自動重試單次成功，狀態回「已同步」 |
| E2E-17a | 退避第 1 次顯示 30 秒（Scenario 17 列 1） | 首次 429 | 狀態列顯示「速率限制（429），30 秒後重試」 |
| E2E-17b | 退避第 2 次顯示 60 秒（Scenario 17 列 2） | 連續第 2 次 429 | 狀態列顯示「速率限制（429），60 秒後重試」 |
| E2E-17c | 退避第 3 次顯示 120 秒（Scenario 17 列 3） | 連續第 3 次 429 | 狀態列顯示「速率限制（429），120 秒後重試」 |
| E2E-18 | 背景不輪詢、回前景立即檢查（Scenario 18） | tab 切至背景→`page.clock` 快轉 120s（背景）→ mock 雲端被 A 更新→切回前景 | 背景期間無 kvdb 請求；回前景立即一次同步並收到變更；前景每 60s 持續檢查 |
| E2E-19 | 停用同步後本地保留（Scenario 19） | 已配對含 X → 點「停用」 | 狀態列「未啟用同步」；後續 kvdb 請求計數不再增加；本地 X 保留且可正常操作 |
| E2E-20 | 停用後重新啟用（Scenario 20） | 承 E2E-19 → 再貼配對碼 → 點「啟動」 | 狀態列「同步中…」→ 與雲端既有清單合併 → 重新納入同步 |
| E2E-21 | 匯出追蹤清單（Scenario 21） | 含追蹤 X（+ETF）→ 展開「匯出/匯入」→ 點「匯出追蹤清單」 | 取得匯出文字/分享連結；內容為目前追蹤項目（不含已移除） |
| E2E-22 | 匯入合併且不重複（Scenario 22） | 本地含 X；匯入文字含 X、Y → 貼上 → 點「匯入」 | X 維持一筆、Y 加入清單 |
| E2E-23 | 匯入格式錯誤（Scenario 23） | 本地含 X → 貼上格式錯誤內容 → 點「匯入」 | 顯示錯誤提示；本地清單仍只有 X |
| E2E-24 | 配對碼無效（Scenario 24） | mock kvdb 對該 token 回 401 → 貼上無效配對碼啟動 | 狀態列「同步失敗」附錯誤訊息；本機清單不受影響；改貼正確配對碼後恢復同步 |
| E2E-25 | 配對碼過期持續失敗（Scenario 25） | mock kvdb 持續回 401 → 貼上過期配對碼 | 同步持續失敗並顯示錯誤訊息；本機清單不受影響 |
| E2E-26 | localStorage 不可用視同未配對（Scenario 26） | `addInitScript` 覆寫 localStorage 使 setItem 拋錯 → 貼配對碼啟動 | 配對碼無法記住；裝置視同未啟用同步；追蹤既有操作維持正常 |
| E2E-27 | 舊版資料載入沿用（Scenario 27） | 預先寫入舊格式資料（無 updatedAt）→ 開啟 /watchlist → 啟用同步 | 舊資料正常載入顯示；未啟用時操作與先前一致；啟用後舊資料參與合併成功 |

### 3.7 kvdb mock 策略（E2E 基礎設施）

```typescript
// e2e/helpers/kvdbMock.ts —— 建議共用 helper
import { Page } from '@playwright/test'

/** 記憶體文件儲存：同一測試內多 tab（page）共享 = 多裝置語意 */
export function installKvdbMock(page: Page, store: Map<string, any>) {
  return page.route('https://kvdb.io/**', async (route) => {
    const url = new URL(route.request().url())
    const key = url.pathname.split('/').pop() ?? ''
    const token = url.searchParams.get('access_token') ?? ''
    const behavior = mockByToken.get(token) // { mode: 'ok' | '404' | '429' | 'fail' | 401 }
    if (behavior?.mode === 'fail') return route.abort('failed')
    if (behavior?.mode === '429') return route.fulfill({ status: 429 })
    if (behavior?.mode === '401') return route.fulfill({ status: 401 })

    if (route.request().method() === 'GET') {
      if (behavior?.mode === '404' || !store.has(key)) return route.fulfill({ status: 404, body: '' })
      return route.fulfill({ status: 200, json: store.get(key) })
    }
    if (route.request().method() === 'POST') {
      store.set(key, route.request().postDataJSON())
      return route.fulfill({ status: 200, body: '' })
    }
    return route.fulfill({ status: 405 })
  })
}
```

要點：

- **多裝置語意**：同一 `Map` 傳給兩個 page 的 mock → tab A 寫回、tab B 拉取，模擬兩台裝置共用雲端。
- **行為切換**：測試中途改 `mockByToken.get(token).mode`（如 fail→ok）即可模擬「恢復連線」「離線期間→正常」。
- **計時器**：60s 輪詢、429 退避、1.5s debounce 使用 `page.clock.install()`（`fastForward('01:00')` 等），避免真實等待造成測試不穩定。
- **請求計數**：E2E-02/05/19 透過 route 內計數器驗證「零請求／停止請求」。

---

## 4. 手動驗證（真實環境）

> 僅放入自動化無法取代的真實環境情境（真實 kvdb、真實雙裝置、真實瀏覽器隱私模式）。

| # | 情境 | 驗證步驟 | 預期 |
|---|------|---------|------|
| MAN-01 | 雙裝置真實 kvdb 同步 | 手機與電腦分別取得同一配對碼並貼上啟用；手機新增股票 → 電腦切回 /watchlist；電腦移除股票 → 手機切回；停留前景 60 秒觀察自動檢查；點「立即同步」；飛機模式（離線）下手機增刪 → 恢復連線後切回頁面 | 兩邊清單最終一致；移除傳播（墓碑）；60s 輪詢與立即同步皆生效；離線操作不消失、恢復後自動合併且不需重貼配對碼（對應 BDD Scenario 8/9/10/11/13/14/15 之真實環境版） |
| MAN-02 | 配對碼外流回收 | 使用者 A 配對碼疑似外流 → 擁有者依 README 產生新 token（同 prefix）並交付 A → 舊碼裝置同步失敗、新碼裝置恢復；確認新 token 無法讀寫其他 prefix（越界被拒） | 舊碼立即失效（同步失敗、本地清單不受影響）；換新碼後恢復同步；越界存取被 kvdb 拒絕（對應交互流程 §5 異常處理「配對碼外流」） |
| MAN-03 | 真實隱私模式（localStorage 不可用） | 開啟瀏覽器無痕/隱私視窗（隱私模式阻擋 localStorage 的環境）→ 貼配對碼啟動 → 執行追蹤操作 | 配對碼無法記住、裝置視同未啟用同步（同步引擎不啟動）；追蹤清單既有操作行為維持正常（對應 BDD Scenario 26） |

---

## 5. 測試環境

| 項目 | 需求 |
|------|------|
| Node.js | v22.23.1（本機實測） |
| Vue | ^3.4.0（Composition API） |
| Vite | ^5.4.0（`frontend/vite.config.ts` 內嵌 vitest 設定：`environment: 'happy-dom'`、`globals: true`） |
| 單元測試 | Vitest ^2.0.0 + @vue/test-utils ^2.4.0 + happy-dom ^14.0.0 |
| E2E | @playwright/test ^1.62.1（Chromium／Firefox／WebKit） |
| 執行指令 | `npm run test:unit`（`vitest run`）；`npm run test:unit:watch`；`npm run test:e2e`（Playwright）；`npm run test:e2e:ui` |
| E2E 伺服器 | `npm run preview`（baseURL `http://localhost:4173`，`frontend/playwright.config.ts` 自動啟動） |
| 外部依賴模擬 | kvdb.io 一律 stub（`page.route` 或本機測試伺服器）；**E2E 不連真實 kvdb** |
| 測試瀏覽器 | Chromium 為主；Firefox／WebKit 於 CI 或手動補跑 |

---

## 6. 缺陷追蹤模板

| 欄位 | 說明 |
|------|------|
| ID | BUG-SYNC-XXX |
| 測試案例 | 對應 §2/§3/§4 測試編號（如 E2E-09、F-11b、MAN-01） |
| 嚴重程度 | P0（阻擋發佈）／P1（主要）／P2（次要） |
| 重啟步驟 | 逐步操作（含配對碼設定、kvdb mock 模式、clock 設定） |
| 預期 vs 實際 | 對照 BDD Then 與實際結果 |
| 環境 | OS／瀏覽器／Node 版本／配對碼（測試用）／kvdb mock 模式 |

---

## 7. 測試覆蓋矩陣（BDD 追溯）

| BDD Scenario（Feature 行號） | 單元（F-） | E2E | 手動 |
|------------------------------|:---:|:---:|:---:|
| 貼上配對碼啟用同步 | F-01 | E2E-01 | - |
| 配對碼輸入框為空時無法啟動 | F-02 | E2E-02 | - |
| 首次配對（雲端尚無清單）上傳建立 | F-03 | E2E-03 | - |
| 首次配對（雲端已有清單）合併為並集 | F-04 | E2E-04 | - |
| 未配對裝置既有操作行為與現況完全一致 | F-05 | E2E-05 | - |
| 未配對時顯示同步設定區塊 | F-06 | E2E-06 | - |
| 同步狀態列顯示目前同步狀態（Outline 3 列） | F-07a/b/c | E2E-07a/b/c | - |
| 已配對裝置新增追蹤後自動寫回雲端 | F-08 | E2E-08 | MAN-01 |
| 另一台裝置切回頁面即收到新增變更 | F-09 | E2E-09 | MAN-01 |
| 前台每 60 秒自動檢查收到變更 | F-10 | E2E-10 | MAN-01 |
| 移除追蹤以墓碑傳播至另一台裝置 | F-11a/b | E2E-11 | MAN-01 |
| 同一支股票雙端變更以最後寫入者勝出 | F-12 | E2E-12 | MAN-01 |
| 立即同步 | F-13 | E2E-13 | MAN-01 |
| 離線時增刪追蹤正常且本地清單不受影響 | F-14 | E2E-14 | MAN-01 |
| 恢復連線後自動合併離線期間的變更 | F-15 | E2E-15 | MAN-01 |
| 429 速率限制顯示退避訊息並自動恢復 | F-16 | E2E-16 | - |
| 429 退避秒數依 30→60→120 秒遞增（Outline 3 列） | F-17a/b/c | E2E-17a/b/c | - |
| 自動同步僅於頁面可見時執行 | F-18 | E2E-18 | - |
| 停用同步後本地清單保留 | F-19 | E2E-19 | - |
| 停用後重新貼配對碼重新啟用同步 | F-20 | E2E-20 | - |
| 匯出追蹤清單取得可攜帶內容 | F-21 | E2E-21 | - |
| 匯入追蹤清單與本地清單合併且不重複 | F-22 | E2E-22 | - |
| 匯入格式錯誤時顯示錯誤且本地清單不變 | F-23 | E2E-23 | - |
| 配對碼無效時同步失敗且本地清單不受影響 | F-24 | E2E-24 | MAN-02 |
| 配對碼過期（TTL 90 天）時同步持續失敗 | F-25 | E2E-25 | MAN-02 |
| localStorage 不可用時視同未配對 | F-26 | E2E-26 | MAN-03 |
| 舊版追蹤資料可正常載入並沿用 | F-27a/b | E2E-27 | - |

> 追溯說明：25 個 Scenario ＋ 2 個 Scenario Outline（各 3 列 Examples）共 **27 個 BDD 場景區塊**，Examples 每列展開為獨立案例（a/b/c 字尾）→ 每列對應之 31 個場景單位，每個至少對應一項測試案例。

---

## 📝 備註

- **回歸基準**：Phase 5a 既有 `useWatchlist.spec.ts` 與 `watchlist-search.spec.ts` 等測試須全數通過——本功能鐵律為「未配對路徑零影響」。
- **merge 規則來源**：單元案例 F-04/F-11b/F-12/F-27b 直接對應開發規格 §1.4 `merge()` 實作語意（per-item 以 `updatedAt ?? addedAt` 新者勝、墓碑保留）。
- **429 退避**：F-17a/b/c 與 E2E-17a/b/c 對應開發規格 §1.4 `scheduleBackoff()`（30s→60s→120s 指數退避、上限 120 秒）。
- **E2E 不連真實 kvdb**：所有自動化案例以 §3.7 mock 策略隔離外部服務，避免額度耗盡與測試不穩定；真實 kvdb 驗證僅於 MAN-01 手動執行。