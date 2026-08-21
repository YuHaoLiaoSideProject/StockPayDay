/**
 * 配息資料（來自 api/upcoming.json）
 */
export interface UpcomingDividend {
  /** 證券代號，如 "2330" */
  code: string
  /** 證券名稱，如 "台積電" */
  name: string
  /** 證券類型：stock | etf | preferred | 息 */
  type: string
  /** 除權息日，如 "2026-07-25" */
  ex_date: string
  /** 發放日，如 "2026-08-15" */
  pay_date?: string
  /** 現金配息金額 */
  dividend?: number
  /** 現金配息金額（API 格式） */
  cash_dividend?: number
  /** 股票配息金額 */
  stock_dividend?: number
}

/**
 * 行事曆日期格子
 */
export interface CalendarDay {
  /** 日期字串 YYYY-MM-DD */
  date: string
  /** 是否屬於當前月份 */
  isCurrentMonth: boolean
  /** 是否為今天 */
  isToday: boolean
  /** 該日是否有配息 */
  hasDividend: boolean
  /** 該日配息資料（可能為空） */
  dividends: UpcomingDividend[]
}

/**
 * 顯示模式
 */
export type ViewMode = 'calendar' | 'list'

/**
 * 資料載入狀態
 */
export type LoadingStatus = 'loading' | 'success' | 'error' | 'empty'
