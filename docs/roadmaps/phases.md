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
Phase 1: 爬蟲 TWT48U ────→ 取得未來除息預告
Phase 2: 爬蟲 MOPS ──────→ 取得配息日資料
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
- [ ] 目錄結構符合規劃
- [ ] Git 可正常 commit

### 預估工時
0.5 天

---

## Phase 1：爬蟲 TWT48U 🕷️

**目標**：從 TWSE 抓取未來除權除息預告資料

### 資料來源
```
URL: https://www.twse.com.tw/rwd/zh/exRight/TWT48U
方法: GET
參數: response=json
回傳: JSON 格式
資料範圍: 未來 1-2 個月
```

### 交付項目
- [ ] `crawler/sources/twse_twt48u.py` TWT48U 爬蟲
- [ ] `data/twses/{YYYY-MM}.json` 月分檔案
- [ ] 資料合併邏輯（去重）

### 完成定義 (Definition of Done)
- [ ] 執行爬蟲可成功取得 TWT48U 資料
- [ ] `data/twses/` 有月分檔案（如 2026-08.json）
- [ ] 每筆資料包含：code, name, ex_date, type, cash_dividend
- [ ] ex_date 為西元年格式（YYYY-MM-DD）
- [ ] 重複執行不會產生重複資料
- [ ] 執行時間 < 30 秒

### 預估工時
1 天

---

## Phase 2：爬蟲 MOPS 🕷️

**目標**：從 MOPS 抓取配息日（pay_date）資料

### 資料來源
```
URL: https://mops.twse.com.tw/mops/web/t05st09_ifrs
方法: POST
注意: 需要 CSRF Token，回應為 HTML 表格
只擷取: code, ex_date, pay_date
```

### 交付項目
- [ ] `crawler/sources/twse_mops.py` MOPS 爬蟲
- [ ] `data/mops/{YYYY}-Q{N}.json` 季檔案
- [ ] 資料合併邏輯（去重）

### 完成定義 (Definition of Done)
- [ ] 執行爬蟲可成功取得 MOPS 資料
- [ ] `data/mops/` 有季檔案（如 2026-Q3.json）
- [ ] 每筆資料包含：code, ex_date, pay_date
- [ ] 日期格式為西元年（YYYY-MM-DD）
- [ ] 重複執行不會產生重複資料
- [ ] 執行時間 < 60 秒

### 預估工時
1 天

---

## Phase 3：資料處理器 ⚙️

**目標**：將原始資料轉換為前端可用的 API 檔案

### 交付項目
- [ ] `processor/generate_api.py` 主處理腳本
- [ ] `api/upcoming.json` 未來配息資料
- [ ] `api/securities-index.json` 證券清單
- [ ] `api/securities/` 單股歷史檔案

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

## 📁 資料結構總覽

```
data/
├── twses/                        # TWT48U（除息預告）
│   ├── 2026-08.json
│   ├── 2026-09.json
│   └── 2026-10.json
│
└── mops/                         # MOPS（配息日）
    └── 2026-Q3.json
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
