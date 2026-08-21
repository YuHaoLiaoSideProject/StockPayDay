# Phase 7 自動化部署（GitHub Actions） — 開發規格

> **對應 Roadmap**：Phase 7 — `docs/roadmaps/phases.md` 項目 #10
> **技術棧**：Python 3.11+ · GitHub Actions · GitHub Pages
> **Tech Decision**：`docs/tech-decision-stockpayday-2026-07-21.md`
> **操作流程**：`docs/interaction-flows/phases/phase-7-自動化部署.md`
> **BDD**：`docs/bdds/stockpayday.feature`（「自動化部署」章節）
> **測試計畫**：`docs/test-plans/phases/phase-7-自動化部署測試計畫.md`
> **狀態**：設計完成，待開發

---

## 概述

GitHub Actions 每日自動執行爬蟲 + 處理 + 通知 + 部署全流程，實現零人工介入的資料更新與部署。核心包含：

1. **GitHub Actions Workflow**：`.github/workflows/update.yml` — cron 排程 + 手動觸發
2. **Python 環境設定**：3.11 版本、pip 依賴安裝
3. **Pipeline 步驟**：爬蟲 → 處理器 → 通知 → GitHub Pages 部署
4. **錯誤處理**：各步驟失敗時 workflow 標記失敗並通知開發者

---

## 1. 後端實作規格

> 本階段無新 Python 模組，核心工作為 GitHub Actions YAML 設定。
> Python 腳本（`crawler/fetch.py`、`processor/generate_api.py`、`processor/notify.py`）均在先前 Phase 完成。

### 1.1 檔案改動總覽

```
.github/
└── workflows/
    └── update.yml                    ← 新增：GitHub Actions 主 workflow
```

### 1.2 update.yml — GitHub Actions 主 Workflow

```yaml
# .github/workflows/update.yml
# StockPayDay++ 每日自動化：爬蟲 → 處理 → 通知 → 部署
name: Update Dividend Data

on:
  schedule:
    - cron: '0 8 * * *'          # 每日 UTC 08:00（台北時間 16:00）
  workflow_dispatch:              # 支援手動觸發

# 防止同一 workflow 並發執行
concurrency:
  group: update-dividend
  cancel-in-progress: true

jobs:
  update:
    runs-on: ubuntu-latest
    timeout-minutes: 10           # GitHub Actions 免費方案 6 分鐘，留緩衝

    steps:
      # ─── Step 1: Checkout 專案 ───
      - name: Checkout
        uses: actions/checkout@v4

      # ─── Step 2: 設定 Python 環境 ───
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # ─── Step 3: 安裝依賴 ───
      - name: Install dependencies
        run: pip install -r crawler/requirements.txt

      # ─── Step 4: 執行爬蟲 ───
      - name: Run crawler
        run: python crawler/fetch.py

      # ─── Step 5: 執行處理器 ───
      - name: Run processor
        run: python processor/generate_api.py

      # ─── Step 6: 執行通知 ───
      - name: Notify
        if: success()
        run: python processor/notify.py
        env:
          LINE_NOTIFY_TOKEN: ${{ secrets.LINE_NOTIFY_TOKEN }}
        continue-on-error: true  # 通知失敗不影響部署

      # ─── Step 7: 部署至 GitHub Pages ───
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./api
          # 確保 clean 部署（覆蓋舊檔案）
          clean_dir: true
```

### 1.3 Workflow 設定規格

| 設定項 | 值 | 說明 |
|--------|-----|------|
| 觸發方式 | `schedule` + `workflow_dispatch` | cron 每日 UTC 08:00 + 手動觸發 |
| Runner | `ubuntu-latest` | GitHub 免費 runner |
| Python | `3.11` | 與專案要求一致 |
| Timeout | `10` 分鐘 | 安全緩衝（免費方案 6 分鐘限制） |
| 並發控制 | `concurrency` group | 防止重複執行 |
| 通知容錯 | `continue-on-error: true` | 推播失敗不阻斷部署 |
| 部署工具 | `peaceiris/actions-gh-pages@v4` | 成熟的 GitHub Pages 部署 Action |
| 部署目錄 | `./api` | 僅部署前端所需的 API 資料 |

### 1.4 Secrets 設定需求

| Secret | 用途 | 必填 |
|--------|------|:---:|
| `LINE_NOTIFY_TOKEN` | LINE Notify 推播 API Token | 是 |
| `GITHUB_TOKEN` | GitHub Pages 部署權限 | 自動提供 |

---

## 2. 前端實作規格

> 本階段無前端改動。前端已在先前 Phase 完成，此次僅透過 GitHub Pages 部署生效。

**不適用**：Phase 7 為 CI/CD 自動化，不涉及前端程式碼變更。

---

## 3. API 合約

> 本階段無新 API endpoint。

**不適用**：Phase 7 為 GitHub Actions workflow 設定，不涉及後端 API 開發。

---

## 4. 資料流

GitHub Actions 的資料流為單向 pipeline，無需前後端跨層互動：

```
GitHub Actions 觸發（cron / 手動）
  │
  ▼
actions/checkout@v4
  │ 取得專案程式碼
  ▼
actions/setup-python@v5 + pip install
  │ 建立 Python 3.11 環境 + 安裝依賴
  ▼
python crawler/fetch.py
  │ 讀取 MOPS 資料 → 寫入 data/（基底資料）
  ▼
python processor/generate_api.py
  │ 讀取 data/ → 產出 api/（upcoming.json, securities-index.json, securities/）
  ▼
python processor/notify.py
  │ 讀取 api/upcoming.json → 篩選 3 天內配息 → LINE Notify API 推播
  │ ⚠️ continue-on-error：失敗不阻斷部署
  ▼
peaceiris/actions-gh-pages@v4
  │ 將 api/ 目錄部署至 gh-pages branch
  │ GitHub Pages 自動提供靜態檔案
  ▼
GitHub Pages 網站更新
```

**關鍵資料路徑**：

| 資料流 | 輸入 | 輸出 |
|--------|------|------|
| 爬蟲 | MOPS API | `data/raw/`、`data/stocks/`、`data/etfs/`、`data/preferred/` |
| 處理器 | `data/` | `api/upcoming.json`、`api/securities-index.json`、`api/securities/` |
| 通知 | `api/upcoming.json` | LINE Notify API |
| 部署 | `api/` | GitHub Pages (`gh-pages` branch) |

---

## 5. 生命週期

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 排程等待 | GitHub cron | 倒數至 UTC 08:00 | 時間到達 |
| Workflow 啟動 | cron 或手動 | 初始化 runner | runner 就緒 |
| 環境設定 | Workflow 啟動 | checkout + Python + pip | 環境就緒 |
| 爬蟲執行 | 環境就緒 | 執行 fetch.py | 爬蟲完成（成功/失敗） |
| 處理器執行 | 爬蟲成功 | 執行 generate_api.py | 處理完成（成功/失敗） |
| 通知推播 | 處理器成功 | 執行 notify.py | 推播完成（成功/失敗，可容錯） |
| 部署 | 通知完成 | 部署 api/ 至 GitHub Pages | 部署完成 |
| Workflow 結束 | 所有步驟完成 | 回報狀態 | 結束 |

---

## 6. 邊界條件處理

| 情境 | 來源 | 處理方式 |
|------|------|---------|
| 爬蟲失敗 | Interaction Flow 異常處理 | workflow 標記失敗，GitHub 發送通知 |
| 處理器失敗 | Interaction Flow 異常處理 | workflow 標記失敗，GitHub 發送通知 |
| 通知推播失敗 | Tech Decision 風險 | `continue-on-error: true`，不影響部署 |
| 部署失敗 | Interaction Flow 異常處理 | workflow 標記失敗，GitHub 發送通知 |
| GitHub Actions 免費方案 6 分鐘限時 | Tech Decision 風險 | `timeout-minutes: 10`，資料量小通常 1-2 分鐘完成 |
| 同一 workflow 並發執行 | Interaction Flow 邊界 | `concurrency` group 控制，`cancel-in-progress: true` |
| LINE Notify Token 無效 | Phase 6 互動流程 | 401 錯誤，記錄日誌，不阻斷部署 |
| GitHub Pages 快取問題 | Tech Decision 風險 | `clean_dir: true` 確保 clean 部署 |
| TWSE 改版導致爬蟲失效 | Tech Decision 風險 | 監控 workflow 執行結果，失敗時手動檢查 |
| LINE Notify 政策變動 | Tech Decision 風險 | 備案：移除通知步驟，僅保留爬蟲+部署 |
| 無符合 3 天內配息的證券 | Phase 6 互動流程 | notify.py 正常結束，不推播 |
| `upcoming.json` 不存在 | Phase 6 互動流程 | processor 未執行時 notify.py 記錄錯誤 |

---

## 7. CSS 關鍵樣式

> 本階段無前端改動，不涉及 CSS。

**不適用**。

---

## 8. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | 確認 `crawler/fetch.py` 可獨立執行 | Phase 1-2 |
| 2 | 確認 `processor/generate_api.py` 可獨立執行 | Phase 3 |
| 3 | 確認 `processor/notify.py` 可獨立執行 | Phase 6 |
| 4 | 建立 `.github/workflows/update.yml` | #1, #2, #3 |
| 5 | 設定 GitHub Secrets（`LINE_NOTIFY_TOKEN`） | #4 |
| 6 | 手動觸發 workflow 測試 | #4, #5 |
| 7 | 驗證 GitHub Pages 部署結果 | #6 |
| 8 | 驗證 LINE 通知推播 | #6 |
| 9 | 確認 cron 排程正常運作 | #7, #8 |

### DAG 依賴圖

```
#1 爬蟲可執行 ──┐
                 ├──→ #4 建立 workflow ──→ #6 手動測試 ──→ #7 驗證部署 ──→ #9 確認排程
#2 處理器可執行 ──┤                                         │
                 │                                         ▼
#3 通知可執行 ───┘                                    #8 驗證通知
                 ↓
           #5 設定 Secrets
```

---

## 9. 基礎架構設定

### 9.1 GitHub Actions

| 項目 | 設定 |
|------|------|
| Workflow 檔案 | `.github/workflows/update.yml` |
| 觸發排程 | `cron: '0 8 * * *'`（每日 UTC 08:00） |
| 手動觸發 | `workflow_dispatch` |
| Runner | `ubuntu-latest` |
| Python 版本 | `3.11` |
| 並發控制 | `concurrency: { group: update-dividend, cancel-in-progress: true }` |
| Timeout | `10` 分鐘 |

### 9.2 GitHub Pages

| 項目 | 設定 |
|------|------|
| 部署來源 | `gh-pages` branch |
| 部署目錄 | `api/`（前端 build 產出） |
| 部署工具 | `peaceiris/actions-gh-pages@v4` |
| Clean 部署 | `clean_dir: true` |

### 9.3 GitHub Secrets

| Secret | 來源 | 用途 |
|--------|------|------|
| `LINE_NOTIFY_TOKEN` | 手動設定 | LINE Notify API 推播 |
| `GITHUB_TOKEN` | 自動提供 | GitHub Pages 部署權限 |

### 9.4 環境變數

| 變數 | 設定位置 | 預設值 | 說明 |
|------|---------|--------|------|
| `LINE_NOTIFY_TOKEN` | GitHub Secrets | （必填） | LINE Notify API Token |

---

## 10. BDD Scenario 對應追溯

| BDD Scenario | 對應章節 | 實作位置 |
|-------------|---------|---------|
| GitHub Actions 每日自動執行 | §1.2 Workflow、§9.1 | `update.yml` cron 排程 |
| GitHub Actions 手動觸發 | §1.2 Workflow、§9.1 | `update.yml` workflow_dispatch |

### Scenario: GitHub Actions 每日自動執行

```gherkin
Scenario: GitHub Actions 每日自動執行
  Given GitHub Actions cron 排程設定為每日 UTC 08:00
  When 到達排程時間
  Then 自動執行爬蟲
  And 自動執行處理器
  And 自動執行通知
  And 自動部署至 GitHub Pages
```

**對應實作**：
- `on.schedule.cron: '0 8 * * *'` → 每日 UTC 08:00 觸發
- `python crawler/fetch.py` → 自動執行爬蟲
- `python processor/generate_api.py` → 自動執行處理器
- `python processor/notify.py` → 自動執行通知
- `peaceiris/actions-gh-pages@v4` → 自動部署至 GitHub Pages

### Scenario: GitHub Actions 手動觸發

```gherkin
Scenario: GitHub Actions 手動觸發
  Given 開發者在 GitHub repo
  When 開發者點擊 "Run workflow"
  Then 手動觸發 GitHub Actions
  And 執行完整流程
```

**對應實作**：
- `on.workflow_dispatch` → 支援手動觸發
- 所有 steps 依序執行完整流程

---

## 11. 驗收檢查清單

### Workflow 設定
- [ ] `.github/workflows/update.yml` 已建立
- [ ] Cron 排程設定正確（`cron: '0 8 * * *'`）
- [ ] 支援手動觸發（`workflow_dispatch`）
- [ ] 並發控制設定正確

### 環境設定
- [ ] Python 3.11 環境正確設定
- [ ] `crawler/requirements.txt` 依賴安裝成功

### 執行流程
- [ ] 爬蟲可正常執行
- [ ] 處理器可正常執行
- [ ] 通知可正常執行（或容錯跳過）
- [ ] 部署可正常執行

### 錯誤處理
- [ ] 爬蟲失敗時 workflow 標記失敗
- [ ] 處理器失敗時 workflow 標記失敗
- [ ] 通知失敗不影響部署（`continue-on-error: true`）
- [ ] 失敗時 GitHub 有通知

### Secrets 設定
- [ ] `LINE_NOTIFY_TOKEN` 已設定在 GitHub Secrets
- [ ] `GITHUB_TOKEN` 可正常使用

### 部署驗證
- [ ] GitHub Pages 可正常訪問
- [ ] 資料已更新至最新
- [ ] 網站功能正常
