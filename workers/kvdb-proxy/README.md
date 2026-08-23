# kvdb-proxy — Cloudflare Worker 部署指南

> Phase 9 跨裝置追蹤清單同步的後端 proxy，負責建立 kvdb bucket + 產生 access token。

## 架構

```
前端 (Vue)  →  Cloudflare Worker (kvdb-proxy)  →  kvdb.io
  email         建 bucket + 產生 token              雲端 JSON 文件
  ← access_token
```

- **secret_key 安全**：僅存在 Worker 環境變數中，前端永遠看不到
- **免費方案**：Cloudflare Worker 100,000 次/天 + kvdb.io 1,000 req/IP/hr

## 前置需求

1. [Cloudflare 帳號](https://dash.cloudflare.com/sign-up)（免費）
2. [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/)
3. [kvdb.io](https://kvdb.io/) 帳號（免費，取得 secret_key）

## 部署步驟

### 1. 取得 kvdb.io 管理金鑰

1. 前往 [kvdb.io](https://kvdb.io/) 註冊帳號
2. 取得你的 **secret key**（管理金鑰）
3. 決定一個 **signing key**（用來簽發 access token，可自訂任意字串）

### 2. 安裝 Wrangler

```bash
npm install -g wrangler
wrangler login  # 登入 Cloudflare 帳號
```

### 3. 設定 Worker 環境變數

```bash
cd workers/kvdb-proxy

# 設定 secret_key（kvdb.io 管理金鑰）
wrangler secret put SECRET_KEY
# 輸入你的 kvdb.io secret key

# 設定 signing_key（簽發 access token 用）
wrangler secret put SIGNING_KEY
# 輸入你自訂的 signing key
```

### 4. 部署 Worker

```bash
wrangler deploy
```

部署後會得到 Worker URL，例如：
```
https://kvdb-proxy.your-subdomain.workers.dev
```

### 5. 設定前端環境變數

在 `frontend/.env` 或 `frontend/.env.production` 中設定：

```
VITE_SYNC_WORKER_URL=https://kvdb-proxy.your-subdomain.workers.dev
```

### 6. 驗證

```bash
# 測試 Worker API
curl -X POST https://kvdb-proxy.your-subdomain.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# 預期回應：
# {"access_token":"...","bucket_id":"..."}
```

## API 合約

| 方法 | 路徑 | Request | Response | 說明 |
|------|------|---------|----------|------|
| POST | `/` | `{ "email": "user@example.com" }` | `{ "access_token": "...", "bucket_id": "..." }` | 建立帳號 + 產生 token |

### 錯誤回應

| 狀態碼 | 情境 |
|--------|------|
| 400 | 缺少 email 或格式無效 |
| 405 | 非 POST 方法 |
| 502 | kvdb.io 建 bucket / 設 signing_key / 產生 token 失敗 |
| 500 | Worker 內部錯誤 |

## Token 說明

- **TTL**：90 天（7,776,000 秒），到期後需重新輸入 email 產生新 token
- **Prefix**：`user:me:`，限制 token 只能存取 `user:me:*` 前綴的 key
- **Permissions**：`read,write`

## 本地開發

```bash
cd workers/kvdb-proxy
wrangler dev  # 啟動本地 Worker（預設 http://localhost:8787）
```

前端 `.env.development`：
```
VITE_SYNC_WORKER_URL=http://localhost:8787
```

## 注意事項

- secret_key 只存在 Worker 環境變數中，不會暴露給前端
- 每位使用者一個 bucket（由 Worker 自動建立）
- 免費方案限制：Cloudflare Worker 100,000 次/天
- Token 過期後前端會顯示同步失敗，使用者重新輸入 email 即可恢復
