# Phase 9 跨裝置同步 — 替代方案評估：npoint.io

> **評估日期**：2026-08-23
> **評估對象**：https://www.npoint.io 作為 Phase 9（跨裝置追蹤清單同步）的雲端 JSON 後端，取代現行 kvdb.io 方案
> **方法**：官方文件（頁面渲染擷取）+ API 實測（建立 / 讀取 / 寫入 / 快取 / CORS / 速率限制）
> **結論**：**不建議**作為同步後端（詳見 §5）

---

## 0. 摘要

| 維度 | npoint.io 實測結果 | 對 Phase 9 的影響 |
|------|-------------------|-------------------|
| 官方定位 | "one-way JSON store"；API 寫入為 **private beta** | ❌ 核心寫回路徑建立在未正式開放的功能上 |
| 建立 bin | ✅ 匿名 `POST www.npoint.io/documents`（CORS 放行） | ✅ 開通流程可行 |
| 讀取 | ✅ `GET api.npoint.io/{bin}`，無認證 | ✅ |
| 寫入 | ⚠️ `POST api.npoint.io/{bin}` 實測可寫，但未文件化 / private beta；PUT/PATCH/DELETE 瀏覽器被 CORS 擋 | ❌ 契約不穩定 |
| 認證與隔離 | 無寫入認證；無 per-user prefix scope 概念 | ❌ 配對碼=bin id，外流只能重建 bin，無法回收 |
| 快取時效 | GET 走 CDN 共用快取 `max-age=3600`（最長 1 小時） | ⚠️ 「切回頁面即可看到」有時效性風險 |
| 速率限制 | 100 req/min/IP + 600 req/min/bin | ✅ 綽綽有餘 |
| 服務穩定性 | 2026-01 剛改版；一人維護；自承不保證 production | ⚠️ 風險偏高 |

---

## 1. 官方定位與文件要點（頁面渲染實測擷取）

### 1.1 首頁 /docs 明言

> **"n:point is a one-way JSON store: edit online, fetch via GET requests over API. Editing data over the API via POST requests is in private beta. Even once released, n:point is not meant to be a full backend for your app."**

這是本次評估最關鍵的事實：npoint 的設計是「**網站上編輯、API 只讀**」。API 寫入（POST）在 private beta，且官方表態「就算開放也不適合當 app 的完整後端」。

### 1.2 FAQ（api.npoint.io/faq）

- **Is n:point appropriate for use in production?** → 「can't guarantee there won't be brief downtime. It's appropriate to use behind a CDN layer, or for internal tooling.」
- **Is n:point free?** → 「All current features are free, assuming reasonable use (don't hammer the API too hard, or I'll have to add rate-limiting).」— 無正式 SLA、無契約承諾
- **Can I rely on my data staying online permanently?** → 「I will do everything I can... should talk about setting up a paid plan with defined SLAs」— 不保證永久

### 1.3 Changelog（api.npoint.io/changelog）

- **Jan 2026**：「🚧 Updating the site to keep costs under control… n:point has happily been running for 7 years… **costing $500/mo** to run… I will consider a paid tier, but don't have the time to build it out at the moment. My priority is keeping the site online and free. **So I'm updating the site to add usage limits and better caching.**」← 服務正處於「控制成本」的改版期，一人專案
- **Jan 02, 2026**：「Enforce rate-limit of **600 requests per document per minute**」
- **Jan 03, 2026**：「Keep track of the last time a document was accessed via API」
- **Jan 01, 2026**：「Update all libraries. First release after many years!」← 剛大改版，行為可能持續變動

### 1.4 官方功能列表（api.npoint.io/features / premium-features）

- CORS support：`Access-Control-Allow-Origin: *`
- Sub-property access：`/bin/0/description` 可取陣列元素／屬性
- Premium（未開放）：「Edit data via API — using an API POST request (and a secret token, for private bins)」← 寫入被歸類為**付費/未開放**功能

---

## 2. API 實測結果（2026-08-23）

### 2.1 建立 bin（免登入）✅

```
POST https://www.npoint.io/documents
Content-Type: application/json
Body: <新文件 JSON>

→ 200 { token: "<bin id>", api_url: "https://api.npoint.io/<bin id>", ... }
```

- 匿名即可建立（實測成功，bin id = `5568e33ee87cdc1ec525`）
- 瀏覽器 CORS preflight：`Access-Control-Allow-Methods: GET, POST, OPTIONS`、`Access-Control-Allow-Origin: *`、`Access-Control-Allow-Headers: content-type` → **跨來源建立可行**
- ⚠️ `POST https://api.npoint.io/`（舊文件寫的建立方式）實測持續 **500**

### 2.2 讀取 ✅

```
GET https://api.npoint.io/{bin}           → 200 <文件 JSON>
GET https://api.npoint.io/{bin}/{prop}    → 200 子屬性
GET https://api.npoint.io/不存在bin        → 404
```

- 回應有 `Cache-Control: max-age=3600, public`（見 §2.4）

### 2.3 寫入 ⚠️（關鍵問題）

| 方式 | 伺服器端 | 瀏覽器（CORS） | 官方文件 |
|------|---------|---------------|---------|
| `POST api.npoint.io/{bin}`（body=新文件 JSON） | ✅ 實測**確實更新**（200） | ✅ preflight 放行 | ❌ 文件稱 private beta |
| `PUT/PATCH www.npoint.io/documents/{bin}` | ✅ 實測 200（body=`{"contents":"<json string>"}`） | ❌ preflight **無** Access-Control-Allow-Methods / Origin → 瀏覽器直接阻擋 | ⚠️ 舊文件記載，2026 版未更新 |
| `DELETE`（www 與 api 皆試） | ❌ 實測 **500**，測試 bin 刪不掉 | ❌ | ⚠️ |

- **寫入無任何認證（僅限匿名 bin）**：實測 `POST api.npoint.io/{bin}` 直接把內容覆寫成 `null` 再還原成功 → **知道 bin id 就能任意覆寫匿名 bin**
- 寫入形態差異：www PUT 要 `{"contents": "<json 字串>"}`；api POST 是把整個 body 當新文件 — 兩種 host 契約不一致
- 【2026-08-23 原始碼驗證（GitHub `azirbel/npoint` main）】
  - `config/routes.rb`：api 子域名 **只註冊 `GET` 與 `POST /:token`** → `DELETE api.npoint.io/{bin}` 500 是必然（根本沒有 route）；`DELETE/PUT/PATCH www.npoint.io/documents/{token}` 有 route，但 preflight 不放行 = 瀏覽器不可用
  - `api/documents_controller.rb#check_api_update_rights!`：匿名 bin → **直接放行**（無任何驗證）；帳號 bin → 需 `Authorization: Bearer <api_auth_token>` 且 **user 必須 is_premium**，否則 402 →「寫入需 premium」只對帳號 bin 成立
  - `documents_controller.rb#destroy` + `user_can_edit_document`：原始碼中**匿名 bin 任何人皆可刪**（`return true unless document.user.present?`）、帳號 bin 需 owner 否則 401 → 但實測 DELETE www 仍 500 → **部署版行為與 main 分支不一致**（新增保護或 destroy bug），實務上匿名刪除不可用

### 2.4 快取與跨裝置時效 ⚠️

- 所有 GET 回應經 Cloudflare CDN：`cache-control: max-age=3600, public`，實測 `cf-cache-status: MISS / HIT / REVALIDATED` 混用、共享快取有 `age` header（觀察到 age=85s 的快取副本）
- **寫入後同一 CDN edge 1 秒內 GET 即見新值**。此行為已被開源碼證實為刻意設計：`Document#purge_cloudflare_cache`（`after_update`，僅 contents 變更時）會 `CloudflareCache.purge_by_prefix("api.{HOST}/{token}")` 清除該 bin（含子路徑）的 CDN 快取 → **寫入會 purge**，跨裝置時效風險比實測時評估的低（剩餘風險僅 purge 失敗或邊緣節點傳播延遲，官方無 SLA）
- 但 `max-age=3600` 仍在：purge 成功前、或 purge 失敗時，其他裝置最壞仍會讀到 1 小時舊資料

### 2.5 速率限制

- 2026-01 起強制：**100 req/min/IP** + **600 req/min/bin**（跟 kvdb.io 的 1,000 req/IP/hr 約同量級且更結構化）
- 對本設計的耗量估算：每裝置前景輪詢每 60s 一次 + focus 讀取 + 1.5s debounce 寫回 ≈ 每分鐘 2-3 req → **遠低於限制，不構成問題**

### 2.6 服務品質佐證（實測過程觀察）

- 建立 API（api.npoint.io/）回 500、DELETE 回 500、舊文件路徑 404 一片 → 服務處於改版過渡期、文件與實作不一致
- 測試 bin 因 DELETE 失敗無法清乾淨（已還原為無害內容，bin id：`5568e33ee87cdc1ec525`）

---

## 3. 與 kvdb.io（現行方案）對照

| 需求（Phase 9 spec） | kvdb.io | npoint.io | 勝 |
|----------------------|---------|-----------|-----|
| 免登入、純靜態站相容 | ✅ | ✅ | 平 |
| 瀏覽器可讀寫（CORS） | ✅ 實測全方法放行（GET,HEAD,PUT,PATCH,POST,DELETE、origin *、Content-Type/Authorization） | ⚠️ 僅 GET + POST(private beta) 放行 | **kvdb** |
| 寫入 API 正式化 | ✅ token + POST 是正式契約 | ❌ private beta / premium 未開放 | **kvdb** |
| 配對碼=cert 化 access token、可回收 | ✅ token scope 到 key prefix，越界被拒、換 token 即回收 | ❌ bin id 即權限，無回收機制，外流須重建 bin | **kvdb** |
| 多使用者隔離 | ✅ 一人一 key（prefix-scoped） | ❌ 一人一 bin（無 prefix 概念）；同 bin 共用權限 | **kvdb** |
| 跨裝置即時性 | ✅ 直接讀寫（無長效快取） | ⚠️ CDN 快取 max-age=3600、跨 region purge 未保證 | **kvdb** |
| 404＝首次配對語意 | ✅ | ✅ | 平 |
| 額度 | 1,000 req/IP/hr（16/min） | 100 req/min/IP + 600/min/bin | 平（皆足夠） |
| 資料存續 | 免費 key 3 個月 TTL（活資料預期續期） | 無 TTL 機制也無永續保證 | 平 |
| 服務信賴度 | 商用小服務 | 一人專案、2026-01 改版、成本控管期、自承不保 production | **kvdb**（略） |
| 開通新成員成本 | 擁有者 curl 建 bucket + 發 token | 擁有者 curl 建 bin（POST /documents） | 平 |

**核心差異一句話**：kvdb 提供的是「正式、CORS 可用、可認證、可隔離、可回收」的讀寫契約；npoint 提供的是「網站編輯＋公開讀取」的只讀契約，寫入路徑是不公開的 private beta，且完全沒有存取控制。

---

## 4. 若採用 npoint 的可行改造（僅參考）

若仍要評估 npoint（不建議），spec 需改動：

1. `useWatchlistSync` 寫入改用 `POST https://api.npoint.io/<bin>`（body = 整個 `WatchlistSyncDoc`），移除 kvdb 的 `?access_token` 傳參
2. 配對碼 = bin id（+ 網站側設定的 manage secret 僅檔網站編輯，**不影響 API 寫入**）→ 失去「外流換 token 即回收」能力
3. 讀取需自行處理快取時效：在 `WatchlistSyncDoc` 內比較 `updatedAt`，若讀到舊資料且本地較新則立即寫回觸發 purge（仍未保證）
4. 開通流程改為：擁有者 `POST www.npoint.io/documents` 建 bin，把 bin id 交給成員（一次一個 bin 給單一使用者，等同"user:me"）

代價：寫入契約隨時可能被封鎖（private beta → 付費/關閉）、無認證隔離、跨裝置時效不保證 — 同時喪失 Phase 9 §5、§7 的多項安全性與即時性驗收點。

---

## 5. 結論與建議

### 5.1 結論：不建議作為 Phase 9 同步後端

1. **寫入是 private beta**：npoint 官方定位「one-way JSON store」，我們的核心寫回路徑等於押在一個未開放、隨時可能關閉或轉付費的功能上
2. **無認證與隔離**：知道 bin id 就能覆寫（實測驗證）；無 per-user scope、無 token 回收 — 無法滿足 spec §5「配對碼外流 → 換 token 即回收」與驗收 §7「token 越界被拒」
3. **跨裝置即時性**：CDN 共用快取 `max-age=3600`；寫入 purge 有原始碼實作佐證（§2.3），但仍無 SLA、失敗時最壞 1 小時舊資料 —「切回頁面即可看到」仍有結構性不確定性
4. **服務處改版/成本控管期**：Jan 2026 剛大改版、文件與實作不一致（多個 500/404）、一人維護、自承不保證 production — 對照 spec §5「kvdb.io 停擺/改條款」本就列為風險，npoint 的風險更高

### 5.2 建議：維持 kvdb.io 為同步後端

- kvdb.io 方案已於 2026-08-23 spike 實測開通流程（spec §2.3），正式寫入契約 + prefix-scoped token + 全 CORS 放行，符合本階段所有安全與即時性驗收點
- 本次實測再次補強 kvdb CORS 驗證：preflight 全方法放行 ✅（見 §3 表格）

### 5.3 npoint.io 的合適用途（替代方案 A 的骨幹）

npoint 的強項是**唯讀散佈**：免登入匿名建立 + CORS 公開讀取 + 子屬性存取。適合 Phase 9 的「**匯出/匯入備援**」中「分享連結」一環：

```
匯出追蹤清單 → POST www.npoint.io/documents 建立公開 bin → 分享 api.npoint.io/<bin> 連結
對方裝置 → 開啟連結 → GET 讀入 → 合併進本地清單（純讀取，不需 npoint 寫入）
```

- 與「方案 A（URL 分享）」精神一致，且比自訂 URL 方案少建構一個分享頁
- 不碰同步主路徑（仍是 kvdb），任一方停擺都不影響另一方

### 5.4 若納入建議的後續事項

- [ ] （選）匯出/匯入備援採用 npoint 分享連結的可行性細評（spec §6 步驟 8 前置）
- [ ] 已建立之測試 bin `5568e33ee87cdc1ec525`（內容為無害標記）待 npoint 提供刪除能力或自然過期清理