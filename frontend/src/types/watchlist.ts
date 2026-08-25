/**
 * 追蹤清單相關型別
 */

/** 追蹤項目 */
export interface WatchlistItem {
  /** 證券代號，如 "2330" */
  code: string
  /** 加入追蹤的時間戳記 */
  addedAt: number
}

/** 追蹤清單排序方式 */
export type WatchlistSortBy = 'addedAt' | 'code' | 'name' | 'nextDividend'

/** 追蹤清單顯示模式 */
export type WatchlistViewMode = 'calendar' | 'list'
