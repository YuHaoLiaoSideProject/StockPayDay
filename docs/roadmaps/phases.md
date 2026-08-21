# 開發階段規劃：StockPayDay++

## 📋 總覽

| 項目 | 內容 |
|------|------|
| **開發模式** | 敏捷式分階段交付 |
| **總階段數** | 8 個階段 |
| **預估總工時** | ~14 天 |
| **交付原則** | 每個階段可獨立驗收，階段完成後即可使用部分功能 |

---

## 🎯 階段總覽

```
Phase 0: 專案建置 ───────→ 基礎建設完成
Phase 1: 爬蟲（個股）────→ 可抓取個股資料
Phase 2: 爬蟲（ETF+特別股）→ 全部證券資料齊全
Phase 3: 資料處理器 ──────→ 可產生前端用 API
Phase 4: 前端基礎 ────────→ 行事曆/列表可顯示
Phase 5: 前端進階 ────────→ 單股歷史+搜尋
Phase 6: 通知功能 ────────→ LINE 推播上線
Phase 7: 自動化部署 ──────→ GitHub Actions 全自動
Phase 8: 優化打磨 ────────→ RWD + 深色模式 + 體驗優化
```

---

## Phase 0：專案建置 🏗️

**目標**：建立專案骨架，開發環境可運作

### 交付項目
- [ ] 建立完整目錄結構
- [ ] Python 虛擬環境設定
- [ ] `requirements.txt` 建立
- [ ] Vue 3 + Vite + Tailwind 初始化
- [ ] `.gitignore` 設定
- [ ] `README.md` 建立

### 完成定義 (Definition of Done)
- [ ] `pip install -r requirements.txt` 成功
- [ ] `npm install && npm run dev` 成功，可看到 Vue 預設頁面
- [ ] 目錄結構符合 Tech Decision 規劃
- [ ] Git 可正常 commit

### 預估工時
0.5 天

---

## Phase 1：爬蟲 — 個股 🕷️

**目標**：可從 TWSE 抓取個股配息資料並儲存

### 交付項目
- [ ] `crawler/fetch.py` 主腳本
- [ ] `crawler/sources/twse_stock.py` 個股爬蟲模組
- [ ] `data/raw/` 原始資料儲存
- [ ] `data/stocks/` 個股基底資料
- [ ] 資料格式驗證腳本

### 完成定義 (Definition of Done)
- [ ] 執行 `python crawler/fetch.py` 可成功抓取資料
- [ ] `data/raw/` 有 TWSE 原始回應 JSON
- [ ] `data/stocks/` 有個股基底資料（至少 10 支）
- [ ] 每支股票資料包含：code, name, dividend_history
- [ ] 爬蟲可在 2 分鐘內完成

### 預估工時
2 天

---

## Phase 2：爬蟲 — ETF + 特別股 🕷️

**目標**：擴充爬蟲支援所有證券類型

### 交付項目
- [ ] `crawler/sources/twse_etf.py` ETF 爬蟲
- [ ] `crawler/sources/twse_preferred.py` 特別股爬蟲
- [ ] `data/etfs/` ETF 基底資料
- [ ] `data/preferred/` 特別股基底資料
- [ ] 整合測試腳本

### 完成定義 (Definition of Done)
- [ ] ETF 資料正確抓取（至少 10 支，含 0050、0056）
- [ ] 特別股資料正確抓取
- [ ] 所有資料類型可同時抓取
- [ ] 爬蟲錯誤處理完善（網路失敗、資料缺失）
- [ ] 總抓取時間 < 3 分鐘

### 預估工時
1 天

---

## Phase 3：資料處理器 ⚙️

**目標**：將基底資料轉換為前端可用的 API 檔案

### 交付項目
- [ ] `processor/generate_api.py` 主處理腳本
- [ ] `api/upcoming.json` 未來配息資料
- [ ] `api/securities-index.json` 證券清單
- [ ] `api/securities/` 單股歷史檔案
- [ ] 資料格式驗證

### 完成定義 (Definition of Done)
- [ ] 執行 `python processor/generate_api.py` 可成功產出
- [ ] `upcoming.json` 只包含未來配息（ex_date >= 今天）
- [ ] `securities-index.json` 包含所有證券代號+名稱
- [ ] `securities/{code}.json` 每支證券一個檔案
- [ ] 處理時間 < 30 秒

### 預估工時
1.5 天

---

## Phase 4：前端基礎 🎨

**目標**：可顯示行事曆/列表，瀏覽未來配息

### 交付項目
- [ ] Vue 3 路由設定
- [ ] `Home.vue` 首頁
- [ ] `Calendar.vue` 行事曆組件
- [ ] `ListView.vue` 列表組件
- [ ] 載入狀態處理
- [ ] 錯誤狀態處理

### 完成定義 (Definition of Done)
- [ ] 開啟網站顯示行事曆模式
- [ ] 行事曆正確顯示當月份
- [ ] 有配息的日期有視覺標示
- [ ] 可切換行事曆/列表模式
- [ ] 列表依日期排序
- [ ] 資料載入中顯示 spinner
- [ ] 載入失敗顯示錯誤訊息

### 預估工時
2 天

---

## Phase 5：前端進階 🔍

**目標**：可查看單股歷史、搜尋股票

### 交付項目
- [ ] `Stock.vue` 單股歷史頁面
- [ ] `SearchBar.vue` 搜尋組件
- [ ] 行事曆日期點擊互動
- [ ] 列表股票點擊互動
- [ ] 返回導航

### 完成定義 (Definition of Done)
- [ ] 點擊行事曆日期顯示該日配息股票
- [ ] 點擊股票導航至歷史頁面
- [ ] 歷史頁面正確顯示配息紀錄
- [ ] 返回按鈕可回首頁
- [ ] 搜尋欄可輸入代號或名稱
- [ ] 即時顯示搜尋結果
- [ ] 點擊搜尋結果導航至歷史頁面
- [ ] 無搜尋結果顯示提示

### 預估工時
1.5 天

---

## Phase 6：通知功能 📢

**目標**：配息日前自動推播 LINE 通知

### 交付項目
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
0.5 天

---

## Phase 7：自動化部署 🤖

**目標**：GitHub Actions 每日自動爬蟲+部署

### 交付項目
- [ ] `.github/workflows/update.yml`
- [ ] GitHub Pages 設定
- [ ] Secrets 設定（LINE_NOTIFY_TOKEN）
- [ ] 手動觸發測試

### 完成定義 (Definition of Done)
- [ ] GitHub Actions 可手動觸發成功
- [ ] 爬蟲 → 處理 → 通知 → 部署流程完整
- [ ] GitHub Pages 可正常訪問
- [ ] Cron 每日自動執行
- [ ] 失敗時 GitHub 有通知

### 預估工時
0.5 天

---

## Phase 8：優化打磨 ✨

**目標**：響應式設計、深色模式、體驗優化

### 交付項目
- [ ] RWD 響應式設計
- [ ] 深色模式
- [ ] 空狀態設計
- [ ] 載入動畫優化
- [ ] 最終測試

### 完成定義 (Definition of Done)
- [ ] 手機版（< 768px）正常使用
- [ ] 平板版（768px - 1024px）正常使用
- [ ] 深色模式切換正常
- [ ] 空狀態有適當提示
- [ ] 整體流暢度良好

### 預估工時
1.5 天

---

## 📊 階段依賴關係

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5
                 │                       │
                 └───────────────────────┴──→ Phase 6
                                                      │
                                                      ↓
                                              Phase 7 ──→ Phase 8
```

**可並行**：
- Phase 4（前端）可與 Phase 3（處理器）部分並行，使用假資料開發
- Phase 6（通知）可獨立開發

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
