# 開發階段規劃：StockPayDay++

## 📋 總覽

| 項目 | 內容 |
|------|------|
| **開發模式** | 敏捷式分階段交付 |
| **總階段數** | 9 個階段（Phase 6 已取消，實際實作 8 個） |
| **預估總工時** | ~19 天 |
| **完成進度** | ✅ 已完成 9 個（Phase 0-5、7-9）｜⛔ 取消 1 個（Phase 6） |
| **交付原則** | 每個階段可獨立驗收，階段完成後即可使用部分功能 |

---

## 🔑 技術決策摘要（整併自 StockPayDay++ 基礎決策）

| 方案 | 描述 | 結果 |
|------|------|------|
| 🟢 靜態站 + GitHub Actions | 爬蟲 + JSON + GitHub Pages | ✅ **採用** |
| 🟡 Serverless + Supabase | 爬蟲 + PostgreSQL + Vercel | ❌ 過度設計 |
| 🔵 全端框架 | FastAPI + SQLite | ❌ 維運成本高 |

**選擇理由**：配息資料更新頻率低（每日一次足夠）、小群體使用（免費方案綽綽有餘）、零維運（無伺服器/資料庫）、資料結構簡單（JSON 完全夠用）。資料分層：`data/`（基底）→ `processor/` → `api/`（前端用），每支證券獨立檔案方便查詢歷史。

## 🎯 階段總覽

```
Phase 0: 專案建置 ───────→ ✅ 基礎建設完成（2026-08-21）
Phase 1: 爬蟲 TWT48U ────→ ✅ 已實作（現預設改為 MoneyDJ 來源）
Phase 2: 爬蟲 MOPS ──────→ ✅ 已實作（現預設改為 MoneyDJ 來源）
Phase 3: 資料處理器 ──────→ ✅ API 產出已上線
Phase 4: 前端基礎 ────────→ ✅ 行事曆/列表上線
Phase 5: 前端進階 ────────→ ✅ 單股歷史+搜尋+追蹤清單
Phase 6: 通知功能 ────────→ ⛔ 已取消（移除 LINE Notify）
Phase 7: 自動化部署 ──────→ ✅ GitHub Actions + Pages 上線
Phase 8: 優化打磨 ────────→ ✅ RWD + 深色模式完成
Phase 9: 跨裝置同步 ──────→ ✅ 已完成（2026-08-24）
```

---

## Phase 0：專案建置 🏗️

**目標**：建立專案骨架，開發環境可運作

**狀態**：✅ **已完成**（2026-08-21，commit `cd174f2`）

### 交付項目
- [x] 建立完整目錄結構
- [x] Python 虛擬環境設定
- [x] `requirements.txt` 建立
- [x] Vue 3 + Vite + Tailwind 初始化
- [x] `.gitignore` 設定
- [x] `README.md` 建立

### 完成定義 (Definition of Done)
- [x] `pip install -r requirements.txt` 成功
- [x] `npm install && npm run dev` 成功，可看到 Vue 預設頁面
- [x] 目錄結構符合規劃
- [x] Git 可正常 commit

### 預估工時
0.5 天

---

## Phase 1：爬蟲 TWT48U 🕷️

**目標**：從 TWSE 抓取未來除權除息預告資料

**狀態**：✅ **已完成**（2026-08-21 實作，commit `a0eed74`；2026-08-23 起預設配息來源改為 MoneyDJ，TWT48U 仍可透過 `--source twses` / `--source twses-mops` 切換）

### 資料來源
```
URL: https://www.twse.com.tw/rwd/zh/exRight/TWT48U
方法: GET
參數: response=json
回傳: JSON 格式
資料範圍: 未來 1-2 個月
```

### 交付項目
- [x] `crawler/sources/twse_twt48u.py` TWT48U 爬蟲
- [x] `data/twses/{YYYY-MM}.json` 月分檔案
- [x] 資料合併邏輯（去重）

### 完成定義 (Definition of Done)
- [x] 執行爬蟲可成功取得 TWT48U 資料
- [x] `data/twses/` 有月分檔案（如 2026-08.json）
- [x] 每筆資料包含：code, name, ex_date, type, cash_dividend
- [x] ex_date 為西元年格式（YYYY-MM-DD）
- [x] 重複執行不會產生重複資料
- [x] 執行時間 < 30 秒

### 預估工時
1 天

---

## Phase 2：爬蟲 MOPS 🕷️

**目標**：從 MOPS 抓取配息日（pay_date）資料

**狀態**：✅ **已完成**（MOPS 爬蟲已實作並通過測試；2026-08-23 起預設配息來源改為 MoneyDJ，MOPS 仍可透過 `--source mops` / `--source twses-mops` 切換）

### 資料來源
```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
注意: 需要 CSRF Token，回應為 HTML 表格
只擷取: code, ex_date, pay_date
```

### 交付項目
- [x] `crawler/sources/mops_dividend.py` MOPS 爬蟲（原規劃檔名 `twse_mops.py`）
- [x] `data/mops/{YYYY}-Q{N}.json` 季檔案
- [x] 資料合併邏輯（去重）

### 完成定義 (Definition of Done)
- [x] 執行爬蟲可成功取得 MOPS 資料
- [x] `data/mops/` 有季檔案（如 2026-Q3.json）
- [x] 每筆資料包含：code, ex_date, pay_date
- [x] 日期格式為西元年（YYYY-MM-DD）
- [x] 重複執行不會產生重複資料
- [x] 執行時間 < 60 秒

### 預估工時
1 天

---

## Phase 3：資料處理器 ⚙️

**目標**：將原始資料轉換為前端可用的 API 檔案

**狀態**：✅ **已完成**（2026-08-21 上線，`generate_api.py` 支援多種來源切換）

### 交付項目
- [x] `processor/generate_api.py` 主處理腳本
- [x] `api/upcoming.json` 未來配息資料
- [x] `api/securities-index.json` 證券清單
- [x] `api/securities/` 單股歷史檔案

### 完成定義 (Definition of Done)
- [x] 執行 `python processor/generate_api.py` 可成功產出
- [x] `upcoming.json` 只包含未來配息（ex_date >= 今天）
- [x] `securities-index.json` 包含所有證券代號+名稱（含上市/上櫃）
- [x] `securities/{code}.json` 每支證券一個檔案（截至 2026-08-23 共 2,764 支）
- [x] 處理時間 < 30 秒

### 預估工時
1.5 天

---

## Phase 4：前端基礎 🎨

**目標**：可顯示行事曆/列表，瀏覽未來配息

**狀態**：✅ **已完成**（2026-08-21，commit `069dcdf`）

### 交付項目
- [x] Vue 3 路由設定
- [x] `Home.vue` 首頁
- [x] `Calendar.vue` 行事曆組件
- [x] `ListView.vue` 列表組件
- [x] 載入狀態處理
- [x] 錯誤狀態處理

### 完成定義 (Definition of Done)
- [x] 開啟網站顯示行事曆模式
- [x] 行事曆正確顯示當月份
- [x] 有配息的日期有視覺標示
- [x] 可切換行事曆/列表模式
- [x] 列表依日期排序
- [x] 資料載入中顯示 spinner
- [x] 載入失敗顯示錯誤訊息

### 預估工時
2 天

---

## Phase 5：前端進階 🔍

**目標**：可查看單股歷史、搜尋股票

**狀態**：✅ **已完成**（2026-08-21，commit `7ee6ae8`；另衍生 Phase 5a「追蹤任意股票」亦已完成）

### 交付項目
- [x] `Stock.vue` 單股歷史頁面
- [x] `SearchBar.vue` 搜尋組件
- [x] 行事曆日期點擊互動
- [x] 列表股票點擊互動
- [x] 返回導航

### 完成定義 (Definition of Done)
- [x] 點擊行事曆日期顯示該日配息股票
- [x] 點擊股票導航至歷史頁面
- [x] 歷史頁面正確顯示配息紀錄
- [x] 返回按鈕可回首頁
- [x] 搜尋欄可輸入代號或名稱
- [x] 即時顯示搜尋結果
- [x] 點擊搜尋結果導航至歷史頁面
- [x] 無搜尋結果顯示提示

### 衍生功能 Phase 5a：追蹤任意股票（2026-08-22 完成）
- [x] 搜尋結果加 ❤️ 加入追蹤清單（localStorage，`useWatchlist.ts`）
- [x] 追蹤清單頁面 + 導覽列徽章（`WatchlistView.vue`）
- [x] 搜尋支援上櫃（TPEx）證券
- 文件：`docs/bdds/001-追蹤任意股票.feature`、`docs/tech-decisions/001-追蹤任意股票.md`

### 預估工時
1.5 天

---

## Phase 6：通知功能 📢

**狀態**：⛔ **已取消**（2026-08-21，commit `df76ba2` 移除 LINE Notify 通知功能）

> 背景：原規劃於配息日前以 LINE Notify 推播通知，開發期間決定移除：
> - 刪除 `processor/notify.py`
> - 從 GitHub Actions workflow 移除通知步驟
> - 不再需要 `LINE_NOTIFY_TOKEN`（`.env.example` 中的設定已無作用，可忽略）

### 原始交付項目（保留供參考，均已不採用）
- [ ] `processor/notify.py` 通知腳本
- [ ] LINE Notify token 設定
- [ ] 通知內容格式
- [ ] 通知篩選邏輯（3 天內）

### 完成定義 (Definition of Done)
- [ ] 執行 `python processor/notify.py` 可推播
- [ ] 只通知 3 天內要除權息的證券
- [ ] 通知內容包含：代號、名稱、除權息日、金額
- [ ] 格式清晰易讀
- [ ] 無符合條件時不推播（避免空訊息）

### 預估工時
~~0.5 天~~

---

## Phase 7：自動化部署 🤖

**目標**：GitHub Actions 每日自動爬蟲+部署

**狀態**：✅ **已完成**（2026-08-21 起上線並持續運作；另有 `ci.yml` 於 push/PR 自動跑測試）

### 交付項目
- [x] `.github/workflows/update.yml`
- [x] `.github/workflows/ci.yml`（push / PR 自動驗證）
- [x] GitHub Pages 設定（`actions/deploy-pages` 部署）
- [x] 手動觸發測試（`workflow_dispatch` + `run_crawler` 選項）
- 備註：通知功能取消後無需任何 repository Secrets；LINE_NOTIFY_TOKEN 不復存在

### 完成定義 (Definition of Done)
- [x] GitHub Actions 可手動觸發成功
- [x] 爬蟲 → 處理 → 部署流程完整（通知步驟已隨 Phase 6 移除）
- [x] GitHub Pages 可正常訪問
- [x] Cron 每日自動執行（UTC 08:00；爬蟲後自動 commit `data/` 回 repo）
- [x] 失敗時 GitHub 有通知

### 預估工時
0.5 天

---

## Phase 8：優化打磨 ✨

**目標**：響應式設計、深色模式、體驗優化

**狀態**：✅ **已完成**（2026-08-22，含 Google 行事曆風格 UIUX 重設計與 Playwright E2E 測試）

### 交付項目
- [x] RWD 響應式設計
- [x] 深色模式（`useDarkMode.ts`，支援系統偏好）
- [x] 空狀態設計
- [x] 載入動畫優化
- [x] 最終測試（vitest 單元 + Playwright E2E + CI 全自動）

### 完成定義 (Definition of Done)
- [x] 手機版（< 768px）正常使用
- [x] 平板版（768px - 1024px）正常使用
- [x] 深色模式切換正常
- [x] 空狀態有適當提示
- [x] 整體流暢度良好

### 預估工時
1.5 天

---

## Phase 9：跨裝置追蹤清單同步 🔄

**目標**：追蹤清單可跨裝置自動同步（免登入、保持純靜態站）

**狀態**：✅ **已完成**（2026-08-24，含同步引擎 + 設定 UI + 匯出匯入 + 單元測試 + E2E）

### 決策依據
- **Tech Decision**：本階段決策已整併至此文件（原 `docs/tech-decisions/010-跨裝置追蹤清單同步.md` 已移除）
- 方案：kvdb.io 共享 JSON + access token 配對（開通流程已於 2026-08-23 實測驗證）
- 關鍵決定：雙向自動同步、免登入、一人一份清單、per-item 最後寫入勝出、offline-first（localStorage 為主）
- 設計原則：**同步為選配**——未貼配對碼的裝置行為與現況完全一致

### 實作參考（2026-08-23 定案）

**kvdb.io 開通流程（已實測）**：
1. 前端 POST kvdb.io（帶 email）→ 自動建立 bucket → 回傳 bucket_id → 存入 localStorage → 開始同步。bucket_id 為隨機字串，難以猜測（透過 obscurity 保護）。

**資料結構（`useWatchlist` 相容擴充）**：
```ts
interface WatchlistItem {
  code: string; name: string; type: 'stock' | 'etf'
  addedAt: number        // 既有欄位
  updatedAt: number      // 新增：同步合併用（舊資料讀取時補 default = addedAt）
  deleted?: boolean      // 新增：墓碑標記（讓「移除」能跨裝置傳播）
}
// 同步文件 = { updatedAt: number, items: WatchlistItem[] }
```

**合併規則**：per-item 最後寫入勝出（依 `code` 並集，單筆以 `updatedAt` 新者勝；`deleted` 視為最終狀態）。僅 foreground 輪詢（每 60s，僅 tab visible）+ focus 讀取；寫回 debounce 1.5s → 先 GET 比對 `updatedAt` 較新才 POST；429 指數退避（30s → 60s → 120s）。配對碼存 `localStorage`（`stockpayday-sync-token`），前端程式碼不含 bucket 金鑰。

**風險登錄**：kvdb.io 停擺/改條款（中/高 → offline-first + 匯出/匯入備援）、429 速率限制（中/中 → 退避）、配對碼外流（低/中 → 換 token 即回收）、免費 key 3 個月過期（低/低 → 活資料預期自動續期）。

### 交付項目
- [x] kvdb.io bucket 建立 + 開通新成員流程文件（README 一節）
- [x] `useWatchlist` 資料模型加 `updatedAt` + 舊資料遷移（向後相容）
- [x] `composables/useWatchlistSync.ts` 同步引擎（拉取/寫回/合併/輪詢/429 退避）
- [x] 設定 UI（配對碼輸入 + 同步狀態顯示）
- [x] 匯出/匯入備援功能
- [x] 合併規則單元測試（per-item last-write-wins、墓碑、並集）＋ E2E 跨 tab 同步測試

### 完成定義 (Definition of Done)
- [x] 兩台裝置各自貼上配對碼，任一裝置增刪股票，另一台切回頁面即可看到
- [x] 離線時本地操作正常，恢復連線後自動合併（per-item 最後寫入勝出）
- [x] 未輸入配對碼的裝置行為與現況完全一致，既有測試全數通過
- [x] 符合速率限制設計：僅前景輪詢 + focus 讀取，429 指數退避
- [x] 配對碼只存 localStorage，前端程式碼不含任何 bucket 金鑰

### 實際工時
P0（模型擴充＋同步引擎＋設定 UI）+ P1（測試＋匯出匯入＋E2E）

---

## 📊 階段依賴關係

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5
                 │                       │
                 └───────────────────────┴──→ Phase 6
                                                      │
                                                      ↓
                                              Phase 7 ──→ Phase 8 ──→ Phase 9 ✅
```

> 註：Phase 6（通知）已於 2026-08-21 取消（移除 LINE Notify），流程跳過該階段；Phase 9 為全新獨立功能，開工時從依賴圖末段延伸。

**可並行**：
- Phase 4（前端）可與 Phase 3（處理器）部分並行，使用假資料開發
- Phase 9（追蹤清單同步）為純前端選配功能，可獨立於爬蟲/部署流程開發

---

## 📁 資料結構總覽（2026-08-23 現況）

```
data/
├── moneydj/                      # MoneyDJ 全市場除權除息（預設來源）
│   ├── 2026-08.json              # 逐月
│   └── ...
│
├── listings/                     # 上市/上櫃證券清單（搜尋索引）
│   ├── 2026-08.json              # 上市（TWSE）
│   └── 2026-08-tpex.json         # 上櫃（TPEx）
│
├── twses/                        # TWT48U 除息預告（--source twses 時使用）
└── mops/                         # MOPS 配息日（舊格式，供 reference）
```

---

## 📋 階段交付檢查表

每個階段完成後，確認以下事項：

| 檢查項目 | 完成 |
|----------|------|
| 功能符合完成定義 | ☐ |
| 程式碼可正常執行 | ☐ |
| 無明顯 Bug | ☐ |
| 文件已更新 | ☐ |
| Git commit 訊息清晰 | ☐ |

---

## 📝 備註

- 每個階段完成後可獨立驗收
- 若某階段發現問題，可暫停並回溯修正
- 預估工時為理想情況，實際可能依複雜度調整
- 建議每階段完成後進行簡短回顧（Retro）
