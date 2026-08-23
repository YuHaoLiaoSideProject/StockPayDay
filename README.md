# StockPayDay++

提醒投資人股利發放日期的工具。

## 功能

- **Crawler**：從臺灣證券交易所（TWSE）與證櫃（TPEx）抓取股利發放資料
- **Processor**：處理原始資料、產生靜態 JSON API、發送 LINE 通知
- **Frontend**：Vue 3 + Vite + Tailwind CSS 靜態站台

## 目錄結構

```
StockPayDay++/
├── crawler/          # 資料爬蟲
├── processor/        # 資料處理與通知
├── frontend/         # Vue 3 前端
├── data/             # 原始與處理後資料（git ignored）
├── api/              # 靜態 JSON API（git ignored）
└── docs/             # 專案文件
```

## 快速開始

### 後端

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## Git Hooks（commit 自動跑測試）

Clone 後執行一次以下指令，之後每次 `git commit` 會自動依暫存內容執行對應測試：

```bash
git config core.hooksPath .githooks
```

- 暫存有 `.py` 檔 → 執行 `pytest`（processor/、crawler/）
- 暫存有前端檔案 → 執行 `vitest run` + 專案建置（`vue-tsc` 型別檢查 + `vite build`）
- 測試或建置失敗會中止 commit；緊急跳過可用 `git commit --no-verify`

另設有 GitHub Actions CI（`.github/workflows/ci.yml`），push / PR 時於遠端自動驗證。

## 自動部署 GitHub Pages

Push 到 `master` 時，GitHub Actions（`.github/workflows/update.yml`）會自動：

1. 以 repo 內 `data/` 重建 `api/`（不執行爬蟲）
2. 建構前端並與 `api/` 組裝
3. 部署至 GitHub Pages

每日排程（UTC 08:00）或手動觸發時才會額外執行爬蟲抓取最新資料。

## 跨裝置同步（Phase 9）

追蹤清單支援跨裝置自動同步，**選配**——未貼配對碼的裝置行為與現況完全一致。同步為 offline-first：本地以 localStorage 為主，離線或同步失敗不影響使用；透過免登入的 kvdb.io 雲端 JSON 存取，維持純靜態站架構。

### 開通新成員（擁有者）

以 curl 三步建立 bucket 並產生配對碼，把回傳的 `access_token=` 值交給成員貼進設定頁：

```bash
# 1) 建立 bucket（免註冊，email 為綁定用；secret_key / write_key 僅開通時使用）
curl https://kvdb.io -d 'email=you@example.com' -d 'secret_key=xxx' -d 'write_key=yyy'

# 2) 設定 signing_key（產生 token 的前置）
curl -X PATCH https://kvdb.io/stockpayday -u '<secret_key>:' -d 'signing_key=<random>'

# 3) 產生 access token（scope 限定單一使用者的 key 前綴）＝配對碼
curl https://kvdb.io/stockpayday/tokens/ -u '<secret_key>:' \
  -d 'prefix=user:<uid>:&permissions=read,write&ttl=7776000'
# 回應 access_token=<token> → 交給成員
```

### 一般使用者

在追蹤清單頁的「跨裝置同步（選配）」設定區貼上配對碼，即開始自動同步：任一裝置增刪追蹤，其他配對裝置切回頁面即自動收到變更。

### 安全

- 配對碼即 access token，只授權單一使用者 key 前綴（`user:<uid>:`），存取其他前綴會被 kvdb.io 拒絕
- 配對碼外流時換發新 token 即回收，不需重建 bucket
- 前端程式碼不含 bucket secret / write key；配對碼只存於瀏覽器 localStorage

## 環境變數

複製 `.env.example` 為 `.env` 並填入：

```bash
LINE_NOTIFY_TOKEN=your_token_here
TWSE_REQUEST_DELAY=2
TWSE_MAX_RETRIES=3
```

## License

MIT
