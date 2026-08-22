# 開發方案決策文件：追蹤清單顯示優化與搜尋範圍擴充

## 📌 決策摘要

| 項目 | 內容 |
|------|------|
| **功能編號** | WATCHLIST-IMPROVE |
| **功能名稱** | 追蹤清單顯示優化與搜尋範圍擴充 |
| **對應 Roadmap** | 功能改善 |
| **決策日期** | 2026-08-22 |
| **共識程度** | 基於上游文件與程式碼分析直接推導 |

---

## 1. 需求回顧

### 核心問題

#### 問題 1：追蹤清單只顯示有「未來配息」的股票

**根因分析**：

```
WatchlistView.vue
  └─ watchlistUpcoming = upcoming.value.filter(item => watchedCodes.has(item.code))
       └─ upcoming.value 來自 useUpcoming() → api/upcoming.json
            └─ generate_upcoming() 只保留 ex_date >= today 的紀錄
```

- `api/upcoming.json` 只包含除權息日在今天或未來的配息紀錄
- 追蹤清單視圖透過 `watchlistUpcoming` 篩選，若追蹤股票的 `ex_date` 全部已過，則在 `upcoming.json` 中找不到對應紀錄
- 結果：已追蹤的股票「消失」在追蹤清單中，即使 `useWatchlist.items` 仍有該股票

**當前程式碼**（`WatchlistView.vue`）：

```typescript
// ❌ 只過濾 upcoming 中有配息的追蹤股票
const watchlistUpcoming = computed<UpcomingDividend[]>(() => {
  return upcoming.value.filter(item => watchedCodes.value.has(item.code))
})

// 這用來決定行事曆要顯示哪些日期 → 同樣受限
const watchlistDividendDates = computed(() => {
  return new Set(watchlistUpcoming.value.map(item => item.ex_date))
})

// isEmpty 檢查 items.length 是正確的，但視圖只渲染 watchlistUpcoming
const isEmpty = computed(() => items.value.length === 0)
```

#### 問題 2：搜尋找不到從未有過配息的股票

**根因分析**：

```
useSearch.ts
  └─ loadIndex() → fetch('./api/securities-index.json')
       └─ generate_securities_index() 只對 data/{stocks,etfs,preferred} 的有紀錄證券去重
            └─ 若股票從未有過配息紀錄，就不在 data/ 目錄中
                 └─ 不在 securities-index.json 中 → 搜尋找不到
```

- `securities-index.json` 由 `processor/generate_api.py` 的 `generate_securities_index()` 產生
- 該函數從 `data/{stocks,etfs,preferred}/*.json` 讀取基底資料，但目前這些目錄為空（0 個檔案）
- 當前 122 筆索引全部來自 TWT48U（除息預告）和 MOPS 的合併結果
- 若某支股票從未出現在 TWT48U/MOPS 中，就沒有任何紀錄，不在索引中

### 用戶期望

| 期望 | 現狀 | 差距 |
|------|------|------|
| 追蹤清單顯示所有已追蹤股票 | 只顯示有未來配息的 | 無未來配息的股票「消失」 |
| 搜尋能找到更多股票 | 只能搜到有配息歷史的 | 從未配息的股票搜不到 |

### 範圍界定

| 項目 | 內容 |
|------|------|
| **包含** | 追蹤清單顯示優化、搜尋資料源擴充 |
| **不包含** | UI/UX 重設計（另有獨立優化文件）、搜尋演算法改進、RWD/深色模式 |
| **相依** | 前端 composable 改動、processor 改動（可選）、新增爬蟲資料源（可選） |

---

## 2. 候選方案

### 問題 1：追蹤清單顯示優化

| 方案 | 描述 | 關鍵差異 |
|------|------|---------|
| **🟢 A. 前端分離：watchlistItems 與 watchlistUpcoming 解耦** | WatchlistView 同時顯示所有追蹤項目（從 `useWatchlist.items`），配息資訊作為附加屬性 | 純前端改動，不改 API |
| **🔵 B. 後端擴充：upcoming.json 加入「無配息」標記** | processor 產出時為所有追蹤股票加入一條紀錄，標記無配息 | 需改 processor + 前端 |
| **🟣 C. 新增 watchlist-full.json API** | processor 額外產出追蹤清單完整資料 | 過度設計，追蹤清單在前端 |

#### 倾向：🟢 方案 A

理由：
1. 追蹤清單完全在前端（localStorage），不應讓後端負責
2. 改動範圍最小（僅 `WatchlistView.vue` + 可能的 `useWatchlist.ts`）
3. 不需要動 processor 或爬蟲
4. 與既有架構一致（前端 composable 處理前端邏輯）

### 問題 2：搜尋範圍擴充

| 方案 | 描述 | 關鍵差異 |
|------|------|---------|
| **🟢 A. 新增 TWSE 證券清單爬蟲 + 合併** | 新增 crawler 從 TWSE 抓取完整上市上櫃清單，processor 合併產出擴充後的 securities-index.json | 爬蟲端 + processor 改動 |
| **🟡 B. 前端即時合併：TWSE 清單 + 現有索引** | 前端在 loadIndex 時同時 fetch TWSE 完整清單 API，合併後搜尋 | 增加前端 fetch 請求，CORS 限制 |
| **🔵 C. 擴充 processor 資料源：從 TWSE 官方 API 合併** | processor 讀取 TWSE 官方上市上櫃清單 JSON，合併到 securities-index.json | 需新增資料目錄 |
| **🟣 D. 僅擴充 data/ 目錄：爬蟲補全個股資料** | 爬蟲抓取所有上市上櫃股票基本資料寫入 `data/stocks/` | 工作量大，需新增爬蟲邏輯 |

#### 倾向：🟢 方案 A

理由：
1. TWSE 有公開的上市上櫃清單 API：
   - 上市：`https://www.twse.com.tw/rwd/zh/afterTrading/OTCStockList`
   - OTC：`https://www.twse.com.tw/rwd/zh/afterTrading/OTCStockList`
2. 資料結構簡單（代號 + 名稱），可獨立爬蟲
3. processor 合併到 `securities-index.json` 是自然延伸
4. 靜態站架構下，一次性產出完整索引比即時 fetch 更穩定

---

## 3. 權衡評估

### 問題 1：追蹤清單顯示優化

| 維度 | 🟢 A. 前端分離 | 🔵 B. 後端標記 | 🟣 C. 新增 API |
|------|:---:|:---:|:---:|
| 🎯 需求符合度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ⚡ 開發速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 🔧 維護成本 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 📈 擴充性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 📦 API 膨脹 | 無 | 無 | 新增檔案 |

**關鍵取捨**：方案 A 純前端改動，最快速；方案 C 雖然彈性高但過度設計（追蹤清單是純前端功能）。

### 問題 2：搜尋範圍擴充

| 維度 | 🟢 A. 新爬蟲+合併 | 🟡 B. 前端即時合併 | 🔵 C. Processor 合併 | 🟣 D. 補全 data/ |
|------|:---:|:---:|:---:|:---:|
| 🎯 需求符合度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| ⚡ 開發速度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 🔧 維護成本 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 🌐 穩定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 📦 資料完整度 | 高 | 中 | 高 | 最高 |

**關鍵取捨**：

- 方案 A（新爬蟲）：新增 TWSE 清單爬蟲，processor 合併到 index → 一次到位，靜態產出
- 方案 B（前端合併）：前端額外 fetch TWSE API → 受 CORS 限制，且 TWSE 非公開 API 可能封鎖跨域
- 方案 D（補全 data/）：最完整但工作量最大，需要爬取所有上市上櫃股票的完整歷史 → 過度投入

---

## 4. 決策理由

### 最終決策

```
┌────────────────────────────────────────────────────────────┐
│  最終決策                                                    │
│                                                            │
│  問題 1：🟢 前端分離方案（WatchlistItems 與 WatchlistUpcoming 解耦）│
│  問題 2：🟢 TWSE 證券清單爬蟲 + Processor 合併                   │
│                                                            │
│  選擇理由：                                                  │
│  1. 追蹤清單是純前端功能，後端不應介入                            │
│  2. TWSE 有公開 API 可取得完整清單，無需自行維護                  │
│  3. 改動範圍精確：前端 composable + 微調 WatchlistView          │
│  4. 靜態站架構下，processor 產出完整 index 是自然延伸            │
│                                                            │
│  共識程度：✅ 基於程式碼分析與既有架構推導                        │
└────────────────────────────────────────────────────────────┘
```

---

## 5. 詳細設計

### 5.1 問題 1：WatchlistView 顯示優化

#### 核心改動：WatchlistView.vue

**改動前**：
```typescript
// ❌ 只顯示有未來配息的追蹤股票
const watchlistUpcoming = computed(() => {
  return upcoming.value.filter(item => watchedCodes.value.has(item.code))
})
```

**改動後**：
```typescript
// ✅ 顯示所有追蹤股票，配息資訊作為附加屬性
const allWatchedItems = computed(() => {
  return items.value.map(item => {
    // 從 upcoming 中查找該股票的配息資料（可能為空）
    const dividend = upcoming.value.find(u => u.code === item.code)
    return {
      ...item,
      dividend, // UpcomingDividend | undefined
      hasUpcomingDividend: !!dividend,
    }
  })
})

// 追蹤股票中有未來配息的（用於行事曆標記）
const watchlistUpcoming = computed(() => {
  return allWatchedItems.value
    .filter(item => item.hasUpcomingDividend)
    .map(item => item.dividend!) // 確認存在
})
```

#### 資料流改動

```
[改動前]
items (useWatchlist) ──┐
                       ├──→ watchlistUpcoming (僅有配息的)
upcoming (useUpcoming) ─┘        │
                                 ▼
                        Calendar / ListView (只顯示配息項)

[改動後]
items (useWatchlist) ──→ allWatchedItems (所有追蹤項目 + 附加配息資訊)
                       │         │
                       │         ├──→ watchlistUpcoming (有配息的，用於行事曆)
                       │         │
                       │         └──→ WatchlistAllItems (所有項目，用於列表)
                       │
upcoming (useUpcoming) ─┘
```

#### 列表模式改動

新增「所有追蹤項目」列表模式，與現有「僅配息」列表並存：

```vue
<!-- 列表模式：顯示所有追蹤股票 -->
<ListView
  v-else
  :items="sortedUpcoming"
  @stock-click="handleStockClick"
/>

<!-- 新增：所有追蹤項目概覽（或作為替代） -->
<div v-else class="watchlist-all-items">
  <div v-for="item in allWatchedItems" :key="item.code" class="watchlist-item">
    <span class="item-code">{{ item.code }}</span>
    <span class="item-name">{{ item.name }}</span>
    <span v-if="item.hasUpcomingDividend" class="item-dividend">
      ${{ item.dividend!.cash_dividend?.toFixed(2) }}
    </span>
    <span v-else class="item-no-dividend">無近期配息</span>
  </div>
</div>
```

#### 行事曆模式改動

保持現有行為（只在行事曆顯示有配息的日期），但新增追蹤清單列表在行事曆下方：

```vue
<!-- 行事曆模式 -->
<Calendar
  v-if="currentView === 'calendar'"
  :month-label="monthLabel"
  :days="days"
  @prev-month="prevMonth"
  @next-month="nextMonth"
  @date-click="handleDateClick"
/>

<!-- 追蹤清單概覽（所有追蹤項目，不管有無配息） -->
<div class="watchlist-all">
  <h3>所有追蹤（{{ items.length }} 支）</h3>
  <div v-for="item in allWatchedItems" :key="item.code" class="watchlist-item-row">
    <span>{{ item.code }} {{ item.name }}</span>
    <span v-if="item.hasUpcomingDividend" class="text-accent">
      ${{ item.dividend!.cash_dividend?.toFixed(2) }}
    </span>
    <span v-else class="text-muted">—</span>
  </div>
</div>
```

#### 涉及檔案

| 檔案 | 改動類型 | 改動說明 |
|------|---------|---------|
| `frontend/src/components/WatchlistView.vue` | 修改 | 新增 `allWatchedItems` computed，改用所有追蹤項目渲染列表 |
| `frontend/src/composables/useWatchlist.ts` | 不改 | 已有 `items` 和 `sortedItems`，足夠使用 |

### 5.2 問題 2：搜尋範圍擴充

#### 策略：新增 TWSE 證券清單爬蟲

**TWSE 上市證券清單 API**：
```
URL: https://www.twse.com.tw/rwd/zh/afterTrading/OTCStockList
方法: GET
參數: response=json
回傳: {
  "stat": "OK",
  "title": "...",
  "data": [
    ["1101", "台泥", "水泥工業", "上市", ...],
    ...
  ]
}
```

> 注意：TWSE 官方端點可能有變動，需定期驗證。若 TWSE 不可用，可用公開資訊觀測站替代。

#### 新增爬蟲模組

```python
# crawler/sources/twse_listing.py

"""
TWSE 上市上櫃證券清單爬蟲

資料來源：
- 上市：TWSE 官方 API
- OTC（上櫃）：TPEX 官方 API（可選）

產出：
- data/listings/{YYYY-MM}.json

格式：
{
  "last_updated": "2026-08-22",
  "source": "TWSE",
  "records": [
    {"code": "1101", "name": "台泥", "market": "TWSE", "industry": "水泥工業"},
    ...
  ]
}
```

#### Processor 改動

```python
# processor/generate_api.py 新增函數

def load_listings() -> List[Dict]:
    """從 data/listings/ 讀取證券完整清單"""
    listings = []
    listings_dir = DATA_DIR / "listings"
    if not listings_dir.exists():
        return listings
    for json_file in sorted(listings_dir.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            listings.extend(data.get("records", []))
    return listings


def generate_securities_index(
    records: List[Dict],
    listings: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    產生證券清單索引

    合併邏輯：
    1. 從 listings 取得完整上市上櫃清單（代號 + 名稱）
    2. 從配息紀錄中補充/更新名稱（以配息紀錄為主）
    3. 去重後輸出
    """
    # 先建立 listings lookup
    listing_lookup: Dict[str, Dict] = {}
    if listings:
        for rec in listings:
            code = rec.get("code", "")
            if code:
                listing_lookup[code] = {
                    "code": code,
                    "name": rec.get("name", ""),
                    "market": rec.get("market", ""),
                    "industry": rec.get("industry", ""),
                }

    # 從配息紀錄建立索引（以此為主，名稱可能更準確）
    seen = set()
    index = []
    for rec in records:
        code = rec["code"]
        if code not in seen:
            seen.add(code)
            # 優先使用配息紀錄的名稱
            name = rec["name"]
            # 若配息紀錄無名稱，從 listings 取得
            if not name and code in listing_lookup:
                name = listing_lookup[code]["name"]
            index.append({
                "code": code,
                "name": name,
            })

    # 補充 listings 中尚未在索引中的股票
    for code, info in listing_lookup.items():
        if code not in seen:
            seen.add(code)
            index.append({
                "code": code,
                "name": info["name"],
            })

    # 排序（依代號）
    index.sort(key=lambda x: x["code"])
    return index
```

#### 前端不需改動

`useSearch.ts` 已從 `securities-index.json` 載入，只要 `securities-index.json` 內容擴充，搜尋自動涵蓋更多股票。

#### 涉及檔案

| 檔案 | 改動類型 | 改動說明 |
|------|---------|---------|
| `crawler/sources/twse_listing.py` | 新增 | TWSE 上市上櫃清單爬蟲 |
| `data/listings/` | 新增目錄 | 存放證券清單資料 |
| `processor/generate_api.py` | 修改 | 新增 `load_listings()`，修改 `generate_securities_index()` 合併清單 |
| `.github/workflows/update.yml` | 修改 | 加入爬蟲步驟 |
| `frontend/src/composables/useSearch.ts` | 不改 | 自動使用擴充後的 index |

---

## 6. 資料流架構圖

### 問題 1 改動後

```
┌─────────────────────────────────────────────────────────────┐
│                        來源資料                               │
├─────────────────────────────────────────────────────────────┤
│ localStorage                                               │
│   └─ stockpayday-watchlist: [{code, name, type, addedAt}]  │
│                                                             │
│ api/upcoming.json                                          │
│   └─ [{code, name, ex_date, cash_dividend, ...}]           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    composables                               │
├─────────────────────────────────────────────────────────────┤
│ useWatchlist()                                             │
│   └─ items: Ref<WatchlistItem[]>  ← 所有追蹤項目             │
│   └─ watchedCodes: computed Set                              │
│                                                             │
│ useUpcoming()                                              │
│   └─ upcoming: Ref<UpcomingDividend[]>  ← 未來配息          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   WatchlistView.vue                          │
├─────────────────────────────────────────────────────────────┤
│ allWatchedItems = items.map(item => {                       │
│   dividend = upcoming.find(u => u.code === item.code)       │
│   return { ...item, dividend, hasUpcomingDividend }         │
│ })                                                         │
│                                                             │
│ ┌─ 行事曆模式 ─────────────────────────────────────────────┐ │
│ │  Calendar (watchlistUpcoming 用於日期標記)                  │ │
│ │  + 所有追蹤項目列表 (allWatchedItems)                      │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─ 列表模式 ───────────────────────────────────────────────┐ │
│ │  所有追蹤項目 (allWatchedItems)，含配息/無配息狀態          │ │
│ └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 問題 2 改動後

```
┌─────────────────────────────────────────────────────────────┐
│                        資料來源                               │
├─────────────────────────────────────────────────────────────┤
│ TWSE 上市上櫃清單 API                                       │
│   └─ {code, name, market, industry}                        │
│                                                             │
│ data/{stocks,etfs,preferred}/*.json (基底歷史)               │
│ data/twses/*.json (除息預告)                                  │
│ data/mops/*.json (配息日)                                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    crawler/sources/twse_listing.py           │
│                    新增：抓取 TWSE 完整清單                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    data/listings/                            │
│                    └─ {YYYY-MM}.json                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    processor/generate_api.py                 │
├─────────────────────────────────────────────────────────────┤
│ generate_securities_index(records, listings):              │
│   1. 從 listings 建立完整清單 lookup                         │
│   2. 從配息紀錄建立索引（以此為主）                           │
│   3. 補充 listings 中尚未在索引中的股票                       │
│   4. 去重 + 排序                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ api/securities-index.json                                   │
│   └─ [{code, name}, ...]                                   │
│      原 122 筆 → 擴充至 ~1,800 筆（全部上市上櫃）              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ frontend/src/composables/useSearch.ts                       │
│   └─ 從 securities-index.json 載入 → 搜尋即涵蓋全部上市上櫃  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 開發任務拆分

### 問題 1：追蹤清單顯示優化（前端）

| # | 任務 | 預估工時 | 優先級 | 依賴 |
|---|------|---------|--------|------|
| 1.1 | WatchlistView 新增 `allWatchedItems` computed | 0.5h | P0 | — |
| 1.2 | 列表模式改為顯示所有追蹤項目（含無配息狀態） | 1h | P0 | #1.1 |
| 1.3 | 行事曆模式新增追蹤項目概覽區 | 0.5h | P1 | #1.1 |
| 1.4 | 更新 useWatchlist 單元測試 | 0.5h | P1 | #1.1 |
| 1.5 | 手動驗證：追蹤無配息股票仍顯示 | 0.5h | P0 | #1.2 |

**預估總工時**：~3 小時

### 問題 2：搜尋範圍擴充（爬蟲 + Processor）

| # | 任務 | 預估工時 | 優先級 | 依賴 |
|---|------|---------|--------|------|
| 2.1 | 研究 TWSE 上市上櫃清單 API 端點 | 1h | P0 | — |
| 2.2 | 實作 `crawler/sources/twse_listing.py` | 2h | P0 | #2.1 |
| 2.3 | 新增 `data/listings/` 目錄與格式設計 | 0.5h | P0 | #2.2 |
| 2.4 | Processor 新增 `load_listings()` | 0.5h | P0 | #2.3 |
| 2.5 | 修改 `generate_securities_index()` 合併清單 | 1h | P0 | #2.4 |
| 2.6 | 更新 `.github/workflows/update.yml` 加入爬蟲 | 0.5h | P0 | #2.2 |
| 2.7 | 撰寫 `generate_securities_index` 單元測試 | 1h | P1 | #2.5 |
| 2.8 | 手動驗證：搜尋能找到更多股票 | 0.5h | P0 | #2.5 |

**預估總工時**：~7 小時

### 總工時

| 面向 | 工時 |
|------|------|
| 問題 1（前端） | ~3h |
| 問題 2（爬蟲+Processor） | ~7h |
| **合計** | **~10h（約 1.25 天）** |

---

## 8. 風險登錄

| 風險 | 可能性 | 影響 | 緩解措施 |
|------|--------|------|---------|
| TWSE API 端點變動或封鎖 | 中 | 中 | 監控爬蟲成功率；備案：使用公開資訊觀測站 |
| securities-index.json 檔案過大 | 低 | 低 | 約 1,800 筆 × ~30 bytes ≈ 54KB，可接受 |
| TWSE 資料含非股票（如權證） | 中 | 低 | 爬蟲端篩選只保留股票/ETF/特別股 |
| 追蹤清單列表改動影響 UX | 低 | 中 | 保持行事曆行為不變，僅優化列表顯示 |
| CORS 問題（若改用前端 fetch） | 高 | 高 | 已選擇後端方案，不涉及 CORS |

---

## 9. 驗證計畫

### 單元測試

| 測試目標 | 檔案 | 說明 |
|----------|------|------|
| `generate_securities_index` 合併 listings | `processor/generate_api_test.py` | 測試 listings 合併到 index 的邏輯 |
| `load_listings` 讀取 listings 資料 | `processor/generate_api_test.py` | 測試 listings 讀取與解析 |
| WatchlistView `allWatchedItems` | `frontend/src/composables/__tests__/useWatchlist.spec.ts` | 測試所有追蹤項目計算 |

### 整合測試

| 測試目標 | 方法 | 說明 |
|----------|------|------|
| 追蹤清單顯示所有項目 | 手動驗證 | 加入一支無配息的股票到追蹤清單，確認在列表模式顯示 |
| 搜尋擴充後的股票 | 手動驗證 | 搜尋一支從未配息的股票，確認能找到 |
| TWSE 爬蟲成功 | `python -m pytest` | 爬蟲端到端測試 |

### 驗收檢查清單

#### 追蹤清單顯示優化
- [ ] 追蹤一支無未來配息的股票，在追蹤清單列表模式可見
- [ ] 追蹤清單列表顯示「無近期配息」或「—」狀態
- [ ] 有未來配息的追蹤股票仍正確顯示配息金額
- [ ] 行事曆模式正確標記有配息的日期
- [ ] 行事曆模式下方顯示所有追蹤項目概覽
- [ ] 追蹤清單為空時仍顯示空狀態引導
- [ ] 移除追蹤後列表立即更新

#### 搜尋範圍擴充
- [ ] `securities-index.json` 包含所有上市上櫃股票（~1,800+ 筆）
- [ ] 搜尋一支從未配息的股票（如新上市公司）能找到
- [ ] 搜尋結果仍限制 10 筆
- [ ] 搜尋無結果時仍顯示「找不到符合的證券」
- [ ] 既有搜尋功能不受影響
- [ ] GitHub Actions 自動執行新爬蟲步驟

---

## 10. 決策後續

| 項目 | 說明 |
|------|------|
| **本文件** | `docs/tech-decisions/009-watchlist-search-improvement.md` |
| **建議執行順序** | 先處理問題 1（純前端，快速驗證），再處理問題 2（爬蟲+Processor） |
| **後續追蹤** | 建議 1 個月後回顧 TWSE API 穩定性 |
| **相關文件** | `docs/uiux/現況UIUX審計與優化建議.md`（P1/P2 問題） |
