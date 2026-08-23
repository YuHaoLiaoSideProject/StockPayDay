# Phase 9 跨裝置追蹤清單同步 — 開發規格

> **對應 Roadmap**：Phase 9 — `docs/roadmaps/phases.md`
> **技術棧**：Vue 3.x (Composition API) · Vite 5.x · Tailwind CSS 3.x · Vitest · Vue Test Utils · Playwright
> **前置階段**：Phase 4（前端基礎）、Phase 5（前端進階）、Phase 5a（追蹤清單）
> **外部依賴**：kvdb.io（免費雲端 JSON 文件，免登入）
> **狀態**：設計完成，待開發

---

## 概述

讓追蹤清單可跨裝置自動同步（免登入、保持純靜態站）。核心包含：

1. **`useWatchlist` 資料模型擴充**：item 增加 `updatedAt`、`deleted` 墓碑（向後相容）
2. **`useWatchlistSync` 同步引擎**：拉取/寫回/合併/輪詢/429 退避
3. **設定 UI**：配對碼輸入＋同步狀態顯示
4. **匯出/匯入備援**：追蹤清單匯出成文字/連結、匯入合併

**設計原則：** 同步為**選配**——未貼配對碼的裝置行為與現況完全一致（localStorage 為主、offline-first），既有測試與使用體驗不受影響。

---

## 1. 前端實作規格

### 1.1 檔案改動總覽

```
frontend/src/
├── types/
│   └── watchlist.ts                  ← 修改：WatchlistItem 加 updatedAt / deleted
├── composables/
│   ├── useWatchlist.ts               ← 修改：remove() 改墓碑語意；add() 帶 updatedAt
│   └── useWatchlistSync.ts           ← 新增：同步引擎（拉取/寫回/合併/輪詢/退避）
├── components/
│   ├── WatchlistView.vue             ← 修改：加入同步狀態列
│   └── WatchlistSyncSettings.vue     ← 新增：配對碼輸入 + 同步狀態顯示
├── views/
│   └── Watchlist.vue                 ← 修改：整合設定 UI（或獨立設定入口）
└── e2e/
    └── watchlist-sync.spec.ts         ← 新增：配對→跨 tab 同步 E2E
docs/
├── roadmaps/phases.md                ← ✅ 已含 Phase 9 決策依據與實作參考
└── README（kvdb bucket 建立 + 開通新成員流程一節）← 交付時新增
```

### 1.2 型別定義 — `types/watchlist.ts`（擴充）

```typescript
/** 追蹤項目（擴充同步欄位，向後相容） */
export interface WatchlistItem {
  /** 證券代號，如 "2330" */
  code: string
  /** 證券名稱，如 "台積電" */
  name: string
  /** 證券類型：stock | etf | preferred */
  type: 'stock' | 'etf' | 'preferred'
  /** 加入追蹤的時間戳記（既有欄位） */
  addedAt: number
  /** 最近一次變更時間戳記（新增：同步合併用；舊資料讀取時補 default = addedAt） */
  updatedAt?: number
  /** 墓碑標記（新增：讓「移除」能跨裝置傳播；deleted: true 視為最終狀態） */
  deleted?: boolean
}

/** 同步文件（kvdb.io 上單一 key 的值） */
export interface WatchlistSyncDoc {
  /** 文件層級最後更新時間（寫回比對用） */
  updatedAt: number
  /** 合併後的追蹤項目（含墓碑） */
  items: WatchlistItem[]
}

/** 同步狀態（供 UI 顯示） */
export type SyncStatus =
  | 'disabled'   // 未輸入配對碼（預設，等同現況）
  | 'idle'       // 已配對，閒置
  | 'syncing'    // 同步中
  | 'synced'     // 最近一次同步成功
  | 'error'      // 同步失敗（含 429 退避中）
```

### 1.3 `useWatchlist` composable（擴充）

職責維持不變：本地追蹤清單管理 + localStorage 持久化。**add()/remove() 補上同步語意，純本地行為不變**。

```typescript
// composables/useWatchlist.ts（修改摘要，僅列變動部分）

const STORAGE_KEY = 'stockpayday-watchlist'

// ...既有 singleton state / init() / watchEffect 不變...

/**
 * 新增追蹤（補 updatedAt）
 */
function add(code: string, name: string, type: WatchlistItem['type'] = 'stock'): void {
  if (isWatched(code)) return
  items.value.push({
    code,
    name,
    type,
    addedAt: Date.now(),
    updatedAt: Date.now(),   // ← 新增
  })
}

/**
 * 移除追蹤 → 改為墓碑語意（同步用）：
 * - 未配對（無 sync）：與現況一致，直接過濾掉該 item
 * - 已配對（有 sync）：保留 item 但標記 deleted: true，由 sync 引擎傳播到其他裝置
 *
 * 對使用者與既有 UI 而言，isWatched() 立即回 false、清單立即消失，行為無感。
 */
function remove(code: string): void {
  if (syncActive) {
    const target = items.value.find(item => item.code === code)
    if (target) {
      target.deleted = true
      target.updatedAt = Date.now()
    }
  } else {
    items.value = items.value.filter(item => item.code !== code)
  }
}

/**
 * 查詢是否已追蹤（含墓碑：deleted 項目視為未追蹤）
 */
function isWatched(code: string): boolean {
  return items.value.some(item => item.code === code && !item.deleted)
}

/** watchedCodes 亦須排除墓碑 */
const watchedCodes = computed(() => {
  return new Set(items.value.filter(item => !item.deleted).map(item => item.code))
})
```

### 1.4 `useWatchlistSync` 同步引擎（新增）

職責：配對碼存在時，負責與 kvdb.io 之間的雙向同步。**無配對碼時整個模組不啟動，零負擔**。

```typescript
// composables/useWatchlistSync.ts（新增）

import { ref, computed, watchEffect, onBeforeUnmount } from 'vue'
import type { WatchlistItem, WatchlistSyncDoc, SyncStatus } from '../types/watchlist'
import { useWatchlist } from './useWatchlist'

const TOKEN_KEY = 'stockpayday-sync-token'
const KVDB_BASE = 'https://kvdb.io'           // bucket 名由擁有者提供，前端不寫死管理金鑰
const BUCKET = 'stockpayday'                  // 約定 bucket（由擁有者建立）
const POLL_INTERVAL_MS = 60_000               // 前景輪詢 60s（僅 tab visible）
const WRITE_DEBOUNCE_MS = 1_500               // 本地變更 → 1.5s debounce 後寫回
const BACKOFF_BASE_MS = 30_000                // 429 指數退避起點：30s → 60s → 120s

const token = ref(localStorage.getItem(TOKEN_KEY) ?? '')
const status = ref<SyncStatus>('disabled')
const lastSyncedAt = ref<number | null>(null)
const lastError = ref<string | null>(null)

const syncActive = computed(() => token.value.length > 0)

// kvdb key：一人一份 → user:<uid>:watchlist
// uid 由擁有者開通時指定（見 README 開通流程），配對碼本身即 access token
function kvKey(): string {
  return 'user:me:watchlist'   // uid 決定於開通時；此處以單一使用者語意簡化
}

// ── 寫回（合併後上傳）──
async function push(localItems: WatchlistItem[]): Promise<void> {
  const now = Date.now()
  const doc: WatchlistSyncDoc = { updatedAt: now, items: localItems }
  const res = await fetch(`${KVDB_BASE}/${BUCKET}/${kvKey()}?access_token=${token.value}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(doc),
  })
  if (res.status === 429) throw new SyncRateLimitedError()
  if (!res.ok) throw new Error(`push failed: ${res.status}`)
}

// ── 拉取 ──
async function pull(): Promise<WatchlistSyncDoc | null> {
  const res = await fetch(`${KVDB_BASE}/${BUCKET}/${kvKey()}?access_token=${token.value}`)
  if (res.status === 404) return null          // 尚未有雲端文件 → 首次推上
  if (res.status === 429) throw new SyncRateLimitedError()
  if (!res.ok) throw new Error(`pull failed: ${res.status}`)
  return await res.json()
}

// ── 合併：per-item 最後寫入勝出（依 code 並集，單筆以 updatedAt 新者勝）──
function merge(localItems: WatchlistItem[], remoteItems: WatchlistItem[] | undefined): WatchlistItem[] {
  const byCode = new Map<string, WatchlistItem>()
  for (const item of [...(remoteItems ?? []), ...localItems]) {
    const prev = byCode.get(item.code)
    if (!prev) {
      byCode.set(item.code, item)               // 新項目直接採用
      continue
    }
    // 單筆以 updatedAt 新者勝出（舊資料無 updatedAt → 以 addedAt 視之）
    const prevT = prev.updatedAt ?? prev.addedAt
    const curT = item.updatedAt ?? item.addedAt
    if (curT > prevT) byCode.set(item.code, item)
  }
  // 墓碑（deleted: true）保留：讓「移除」能在合併後持續傳播
  return [...byCode.values()]
}

// ── 同步主流程：pull → merge → push ──
async function syncOnce(): Promise<void> {
  if (!syncActive.value) return
  status.value = 'syncing'
  try {
    const remote = await pull()
    const { items } = useWatchlist()            // 與現有 singleton 同一份 state
    const merged = merge(items.value, remote?.items)
    items.value = merged
    // 若本地有較新變更（merged ≠ 剛 pull 的 remote，或 remote 為 null）→ 寫回
    await push(items.value)
    lastSyncedAt.value = Date.now()
    status.value = 'synced'
    backoff = 0
  } catch (err) {
    if (err instanceof SyncRateLimitedError) {
      scheduleBackoff()
      lastError.value = `速率限制（429），${Math.round(backoff / 1000)} 秒後重試`
    } else {
      lastError.value = err instanceof Error ? err.message : '同步失敗'
    }
    status.value = 'error'
  }
}

// ── 觸發策略：僅前景輪詢 + focus/visible 即時讀取 ──
let pollTimer: number | undefined
let backoff = 0

function startPolling(): void {
  stopPolling()
  if (!syncActive.value) return
  pollTimer = window.setInterval(() => {
    if (document.visibilityState === 'visible') syncOnce()
  }, POLL_INTERVAL_MS)
}

function stopPolling(): void {
  if (pollTimer !== undefined) clearInterval(pollTimer)
  pollTimer = undefined
}

function onVisibility(): void {
  if (document.visibilityState === 'visible') syncOnce()
}

// 本地變更 → debounce 1.5s 後寫回（先 GET 比 updatedAt，較新才 POST）
watchEffect(() => {
  if (!syncActive.value) return
  const { items } = useWatchlist()
  if (items.value.some(i => i.updatedAt && i.updatedAt > (lastSyncedAt.value ?? 0))) {
    const t = window.setTimeout(() => syncOnce(), WRITE_DEBOUNCE_MS)
    return () => window.clearTimeout(t)
  }
})

function scheduleBackoff(): void {
  backoff = backoff === 0 ? BACKOFF_BASE_MS : Math.min(backoff * 2, 120_000)
  window.setTimeout(() => syncOnce(), backoff)
}

/** 對外 API：設定配對碼 / 清除配對碼 / 手動立即同步 */
function setToken(value: string): void {
  token.value = value.trim()
  localStorage.setItem(TOKEN_KEY, token.value)
  if (token.value) {
    syncOnce()
    startPolling()
  }
}
function clearToken(): void {
  token.value = ''
  localStorage.removeItem(TOKEN_KEY)
  stopPolling()
  status.value = 'disabled'
}

// 初始化：有配對碼才啟動
if (syncActive.value) {
  syncOnce()
  startPolling()
}
document.addEventListener('visibilitychange', onVisibility)
window.addEventListener('focus', onVisibility)
onBeforeUnmount(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('focus', onVisibility)
})

export function useWatchlistSync() {
  return { token, status, lastSyncedAt, lastError, syncActive, setToken, clearToken, syncOnce }
}

class SyncRateLimitedError extends Error {}
```

### 1.5 `WatchlistSyncSettings.vue` 設定 UI（新增）

配對碼輸入＋同步狀態顯示。放在 Watchlist 頁（或設定入口）。

```vue
<!-- components/WatchlistSyncSettings.vue -->

<script setup lang="ts">
/**
 * WatchlistSyncSettings 同步設定
 *
 * - 未配對：顯示配對碼輸入框 + 說明（如何取得配對碼）
 * - 已配對：顯示同步狀態（最後同步時間 / 錯誤）＋清除配對
 */
import { ref } from 'vue'
import { useWatchlistSync } from '../composables/useWatchlistSync'

const { token, status, lastSyncedAt, lastError, setToken, clearToken, syncOnce } = useWatchlistSync()
const input = ref('')

const statusLabel: Record<string, string> = {
  disabled: '未啟用同步',
  idle: '已配對',
  syncing: '同步中…',
  synced: '已同步',
  error: '同步失敗',
}
</script>

<template>
  <section class="watchlist-sync-settings" data-testid="watchlist-sync-settings">
    <!-- 未配對 -->
    <div v-if="!token">
      <h3 class="font-semibold">🔄 跨裝置同步（選配）</h3>
      <p class="text-sm text-text-secondary">
        貼上配對碼後，追蹤清單會在本裝置與其他裝置間自動同步。不設定則完全不影響現有功能。
      </p>
      <form class="flex gap-2 mt-2" @submit.prevent="setToken(input)">
        <input
          v-model="input"
          class="input flex-1"
          placeholder="貼上配對碼（access token）"
          data-testid="sync-token-input"
        />
        <button class="btn btn-primary" type="submit" data-testid="sync-token-submit">啟動</button>
      </form>
    </div>

    <!-- 已配對 -->
    <div v-else class="flex items-center justify-between">
      <div>
        <span class="font-semibold">🔄 同步狀態：{{ statusLabel[status] }}</span>
        <span v-if="lastSyncedAt" class="ml-2 text-xs text-text-muted">
          上次同步 {{ new Date(lastSyncedAt).toLocaleTimeString() }}
        </span>
        <p v-if="lastError" class="text-red-500 text-sm">{{ lastError }}</p>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="syncOnce">立即同步</button>
        <button class="btn btn-danger" @click="clearToken" data-testid="sync-token-clear">
          停用
        </button>
      </div>
    </div>
  </section>
</template>
```

---

## 2. API 合約

本階段無新增自有後端 API。使用外部免費服務 **kvdb.io**（純靜態站相容）。

### 2.1 kvdb.io 契約

| 項目 | 內容 |
|------|------|
| Base URL | `https://kvdb.io/<bucket>` |
| Bucket | `stockpayday`（擁有者建立，bucket secret / write key 只在開通時用，**不進前端程式碼**） |
| Key | `user:<uid>:watchlist`（一人一份；access token 已 scope 到此前綴） |
| 授權 | query string `?access_token=<token>` 或 `Authorization: Bearer <token>`（兩者皆實測可用） |
| 值格式 | `WatchlistSyncDoc`（JSON：`{ updatedAt, items }`） |
| 額度 | 免費 1,000 req/IP/hr |

#### 讀取（GET）

```
GET https://kvdb.io/stockpayday/user:me:watchlist?access_token=<token>
→ 200 { "updatedAt": 1756000000000, "items": [...] }
→ 404 （文件不存在，首次使用）
→ 429 （速率限制）
```

#### 寫入（POST）

```
POST https://kvdb.io/stockpayday/user:me:watchlist?access_token=<token>
Content-Type: application/json

{ "updatedAt": 1756000000000, "items": [...] }
→ 200
→ 429 （速率限制）
```

### 2.2 localStorage 格式（向後相容）

| Key | 值類型 | 說明 |
|-----|--------|------|
| `stockpayday-watchlist` | JSON 陣列 | 追蹤清單陣列（item 新增 `updatedAt`；舊資料無此欄位時視為 `addedAt`） |
| `stockpayday-sync-token` | string | 配對碼（access token）｜**只存 localStorage，不進程式碼** |

```json
// stockpayday-watchlist 範例（含墓碑）
[
  { "code": "2330", "name": "台積電", "type": "stock", "addedAt": 1755900000000, "updatedAt": 1755900000000 },
  { "code": "0056", "name": "元大高股息", "type": "etf", "addedAt": 1755900100000, "updatedAt": 1755910000000, "deleted": true }
]
```

### 2.3 開通新成員流程（擁有者執行一次，README 一節）

```bash
# 1) 建立 bucket（免註冊，email 為綁定用）：
#    curl https://kvdb.io -d 'email=you@example.com' -d 'secret_key=xxx' -d 'write_key=yyy'
# 2) 設定 signing_key（產生 token 的前置）：
curl -X PATCH https://kvdb.io/stockpayday -u '<secret_key>:' -d 'signing_key=<random>'
# 3) 產生 access token（scope 限定單一使用者的 key 前綴）＝配對碼：
curl https://kvdb.io/stockpayday/tokens/ -u '<secret_key>:' \
  -d 'prefix=user:me:&permissions=read,write&ttl=7776000'
#    回應：access_token=<token> → 交給成員貼進設定頁
```

> 越界保護已實測：token 只能存取自己 prefix 下的 key，存取其他 prefix 會被拒絕；外流時換 token 即回收（不需重建 bucket）。

---

## 3. 資料流

```
[裝置 A 使用者增刪追蹤]
       │
       ▼
[useWatchlist.add/remove]  (updatedAt 更新、墓碑)
       │
       ▼
[watchEffect]  debounce 1.5s
       │
       ▼
[useWatchlistSync.syncOnce]
       ├─→ 1. GET kvdb（pull remote doc）
       ├─→ 2. merge(local, remote)  per-item last-write-wins
       ├─→ 3. items 更新 → UI 即時反映
       └─→ 4. POST kvdb（寫回 merged doc）
                     │
                     ▼
              [kvdb.io 雲端文件]
                     │
   ┌─────────────────┴─────────────────┐
   ▼ focus/visible                     ▼ 每 60s 輪詢（僅 tab visible）
[裝置 B 切回頁面]              [裝置 B 前景輪詢]
       ▼                                ▼
[useWatchlistSync.syncOnce] → merge → items 更新 → UI 更新
```

---

## 4. 生命週期

| 階段 | 觸發 | 動作 | 退出條件 |
|------|------|------|---------|
| 初始化 | 頁面載入 | 讀 token；無 token → `disabled`（零負擔）｜有 token → 立即 syncOnce + 啟動輪詢 | 初次同步完成 |
| 本地變更 | add/remove/toggle | watchEffect debounce 1.5s → syncOnce（先 GET 比 updatedAt） | 寫回成功 |
| 前景讀取 | `visibilitychange(visible)` / `window focus` | 立即 syncOnce | merge 完成 |
| 輪詢 | 每 60s（僅 tab visible） | syncOnce | 單次完成 |
| 429 | 任一次請求回 429 | 指數退避 30s → 60s → 120s 後重試單次 | 成功或重試達上限 |
| 停用同步 | 點「停用」 | clearToken → 本地資料保留、停止輪詢 | token 清除 |

---

## 5. 邊界條件處理

| 情境 | 處理方式 |
|------|---------|
| 未輸入配對碼 | 同步引擎完全不啟動，行為與現況 100% 一致（既有測試全數通過） |
| 首次配對（雲端無文件） | GET 404 → merge 本地 → POST 建立 |
| 離線 | 本地操作正常（localStorage 為主）；同步失敗記 `lastError`，恢復連線後由輪詢/focus 自動重試 |
| 多裝置同時編輯同一支 | per-item 最後寫入勝出：以 `updatedAt` 新者勝；極端同刻僅最後 POST 者覆蓋（已接受） |
| 裝置 A 移除、裝置 B 未移除 | 墓碑（`deleted: true`）合併後傳播到 B，B 清單同步移除該支 |
| 舊資料無 `updatedAt` | 遷移時補 `default = addedAt`，合併比對不受影響 |
| 429 速率限制 | 指數退避；僅前景輪詢 + focus 讀取管理額度（1,000 req/IP/hr） |
| 配對碼外流 | 前端無管理金鑰；擁有者換 token 即回收 |
| kvdb.io 停擺 / 改條款 | offline-first，本地資料永不消失；提供匯出/匯入備援；同步介面可遷移替代方案 |
| 免費 key 3 個月過期 | 活資料持續讀寫預期自動續期；必要時付費或換替代方案 |
| localStorage 不可用（隱私模式） | 沿用既有 catch 降級；同步 token 亦無法持久化 → 視同未配對 |

---

## 6. 開發順序

| 步驟 | 內容 | 依賴 |
|------|------|------|
| 1 | kvdb.io bucket 建立＋開通流程實測（Spike 已完成 2026-08-23） | - |
| 2 | `types/watchlist.ts` 加 `updatedAt` / `deleted` / `WatchlistSyncDoc` | - |
| 3 | `useWatchlist` 擴充（add 帶 updatedAt、remove 墓碑語意、isWatched 排除墓碑）＋舊資料遷移 | #2 |
| 4 | `useWatchlistSync` 同步引擎（pull/merge/push/輪詢/退避） | #3 |
| 5 | 合併規則單元測試（per-item last-write-wins、墓碑、並集） | #4 |
| 6 | `WatchlistSyncSettings.vue` 設定 UI | #4 |
| 7 | `WatchlistView.vue` 整合同步狀態列 | #6 |
| 8 | 匯出/匯入備援功能 | #3 |
| 9 | E2E 測試（配對→跨 tab 同步情境） | #6 |
| 10 | README 開通新成員流程一節 | #1 |
| 11 | 手動驗證：雙裝置增刪、離線恢復、未配對不影響現況 | #6, #8 |

---

## 7. 驗收檢查清單（對應 DoD）

### 雙向同步
- [ ] 兩台裝置（或兩個 tab）各自貼上配對碼，任一裝置增刪股票，另一台切回頁面即可看到
- [ ] 移除的股票在另一台也消失（墓碑傳播）
- [ ] 兩台同時操作不同股票 → 並集合併，不遺失

### 離線 / 衝突
- [ ] 離線時本地操作正常
- [ ] 恢復連線後自動合併（per-item 最後寫入勝出）
- [ ] 同股票雙端編輯 → 以 `updatedAt` 新者勝出

### 選配相容
- [ ] 未輸入配對碼的裝置行為與現況完全一致
- [ ] 既有測試（useWatchlist 單元、E2E）全數通過
- [ ] `stockpayday-watchlist` 舊資料（無 updatedAt）可正常載入

### 速率限制
- [ ] 僅前景輪詢（每 60s）+ focus/visible 讀取，背景不輪詢
- [ ] 429 觸發指數退避（30s → 60s → 120s）

### 安全性
- [ ] 配對碼只存 localStorage（`stockpayday-sync-token`）
- [ ] 前端程式碼不含 bucket secret / write key
- [ ] token 越界（存取其他 prefix）被 kvdb 拒絕（實測驗證）

### 設定 UI
- [ ] 配對碼輸入、啟動、停用流程可用
- [ ] 同步狀態（同步中/已同步/失敗＋最後同步時間）正確顯示
- [ ] 匯出/匯入備援功能可用

---

## 8. 測試覆蓋

### 8.1 單元測試（Vitest + Vue Test Utils）

| 測試 | 重點 |
|------|------|
| `merge` 合併規則 | per-item 最後寫入勝出（同 code 新 updatedAt 勝） |
| `merge` 墓碑 | `deleted: true` 為最終狀態，不被本地舊資料覆蓋 |
| `merge` 並集 | 兩端各自獨有的項目皆保留 |
| `merge` 舊資料 | 無 `updatedAt` 時以 `addedAt` 比對 |
| `useWatchlist.remove` 未配對 | 行為與現況一致（直接過濾） |
| `useWatchlist.remove` 已配對 | 寫墓碑、`isWatched` 立即 false |
| `useWatchlist` 遷移 | 舊資料載入後補 `updatedAt = addedAt` |
| `useWatchlistSync` 429 退避 | 觸發 30s → 60s → 120s 排程 |
| localStorage 失敗降級 | setItem/getItem 拋錯不影響其他功能 |

### 8.2 E2E（Playwright）

`watchlist-sync.spec.ts`（模擬 kvdb：可 stub fetch 或 npm 測試伺服器）：

| 情境 | 預期 |
|------|------|
| 未配對裝置操作追蹤 | 行為與現況一致、無同步請求 |
| 貼配對碼 → 兩 tab 即時同步 | tab A 增刪，tab B 切回即看到 |
| 移除傳播 | tab B 移除的股票在 tab A 消失 |
| 離線恢復 | 離線操作，恢復後自動併回 |
| 429 情境 | UI 顯示退避狀態、之後自動恢復同步 |

---

## 9. BDD Scenario 追溯對照表

| BDD Scenario（待補 `.feature`） | 對應組件/Composable | 對應規格章節 |
|---|---|---|
| 跨裝置同步追蹤清單 | useWatchlistSync（syncOnce 全流程） | §1.4, §3 |
| 未配對裝置維持現況 | useWatchlist（無 sync 路徑） | §1.3, §5 |
| 離線後自動合併 | useWatchlistSync（merge + 恢復觸發） | §1.4, §3 |
| 移除跨裝置傳播 | merge 墓碑規則 | §1.4, §5 |
| 設定配對碼 | WatchlistSyncSettings | §1.5 |
| 匯出/匯入備援 | 匯出/匯入功能 | §1.1, §5 |

---

## 📝 備註

- **同步為選配**：這是本階段的鐵律——未輸入配對碼的裝置，code path 不經過任何同步邏輯，既有測試與使用體驗零影響
- 同步介面抽象化：`useWatchlistSync` 內部只依賴 `kvdb.io` 契約；若 kvdb 停擺，可替換為方案 C（自架後端）而不動 `useWatchlist`
- 匯出/匯入是方案 A（URL 分享）精神的備援，也是 kvdb 停擺時的手動逃生門
- 配對碼 = access token，只 scope 單一使用者 prefix；換 token 即回收（不需重建 bucket）
- 開通新成員流程由**擁有者**執行（curl），一般成員只需把 token 貼進設定頁
- 建議實作前先確認：免費方案 key TTL 續期行為（活資料每次寫入是否刷新 3 個月）