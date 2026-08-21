/**
 * 追蹤清單相關型別
 */

/** 追蹤項目 */
export interface WatchlistItem {
  /** 證券代號，如 "2330" */
  code: string
  /** 證券名稱，如 "台積電" */
  name: string
  /** 證券類型：stock | etf | preferred */
  type: 'stock' | 'etf' | 'preferred'
  /** 加入追蹤的時間戳記 */
  addedAt: number
}

/** 追蹤清單排序方式 */
export type WatchlistSortBy = 'addedAt' | 'code' | 'name' | 'nextDividend'

/** 追蹤清單顯示模式 */
export type WatchlistViewMode = 'calendar' | 'list'
