/**
 * 追蹤清單相關型別
 */

/** 追蹤項目 */
export interface WatchlistItem {
  /** 證券代號，如 "2330" */
  code: string
  /** 加入追蹤的時間戳記 */
  addedAt: number
  /** 墓碑標記（讓「移除」能跨裝置傳播；deleted: true 視為最終狀態） */
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
  | 'disabled' // 未輸入配對碼（預設，等同現況）
  | 'idle' // 已配對，閒置
  | 'syncing' // 同步中
  | 'synced' // 最近一次同步成功
  | 'error' // 同步失敗（含 429 退避中）

/** 追蹤清單排序方式 */
export type WatchlistSortBy = 'addedAt' | 'code' | 'name' | 'nextDividend'

/** 追蹤清單顯示模式 */
export type WatchlistViewMode = 'calendar' | 'list'
