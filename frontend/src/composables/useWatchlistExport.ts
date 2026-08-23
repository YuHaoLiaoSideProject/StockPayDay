/**
 * useWatchlistExport — 追蹤清單匯出/匯入備援工具（Phase 9 子任務 C）
 *
 * 職責：純函式將追蹤清單匯出成可攜帶文字（JSON 陣列），以及將匯入文字解析為
 * `WatchlistItem[]`（依 code 去重、格式錯誤拋出可辨識的 `WatchlistImportError`）。
 *
 * 設計原則（§1.1 / §2.2 / §5）：
 * - 匯出僅含「目前追蹤中」（非 deleted 墓碑）的項目
 * - 匯入為備援合併：解析結果由 UI 透過 useWatchlist.add / isWatched 合併，重複 code 不重複加入
 * - 格式錯誤（非 JSON / 非陣列 / 缺少有效 code / 項目非物件）拋錯，本地清單維持不變
 * - 匯入內容中的墓碑（deleted: true）不恢復為追蹤項目
 */
import type { WatchlistItem } from '../types/watchlist'

const VALID_TYPES: ReadonlyArray<WatchlistItem['type']> = ['stock', 'etf', 'preferred']

/** 匯入格式錯誤專屬錯誤：UI 依此顯示可辨識的錯誤訊息 */
export class WatchlistImportError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'WatchlistImportError'
  }
}

/**
 * 匯出追蹤清單為可攜帶文字（JSON 陣列，含 ETF／特別股；不含已移除墓碑項目）
 */
export function exportWatchlistToText(items: WatchlistItem[]): string {
  const active = items.filter(item => item.deleted !== true)
  return JSON.stringify(active, null, 2)
}

/**
 * 解析匯入文字為 WatchlistItem[]（依 code 去重，保留第一筆）。
 *
 * 容錯：
 * - name 缺省 → 以 code 代替
 * - type 非有效值 → 視為 stock
 * - addedAt / updatedAt 非數值 → 以現在時間／addedAt 代替
 * - deleted: true 的項目 → 略過（不恢復已移除項目）
 *
 * 格式錯誤（非 JSON、非陣列、項目非物件、缺少有效 code）→ 拋 WatchlistImportError。
 */
export function parseWatchlistImportText(text: string): WatchlistItem[] {
  let data: unknown
  try {
    data = JSON.parse(text)
  } catch {
    throw new WatchlistImportError('匯入格式錯誤：內容不是有效的 JSON')
  }

  if (!Array.isArray(data)) {
    throw new WatchlistImportError('匯入格式錯誤：內容必須是追蹤清單陣列')
  }

  const seen = new Set<string>()
  const result: WatchlistItem[] = []

  data.forEach((entry, index) => {
    if (entry === null || typeof entry !== 'object') {
      throw new WatchlistImportError(`匯入格式錯誤：第 ${index + 1} 筆不是有效項目`)
    }
    const raw = entry as Record<string, unknown>
    if (typeof raw.code !== 'string' || raw.code.trim() === '') {
      throw new WatchlistImportError(`匯入格式錯誤：第 ${index + 1} 筆缺少有效的證券代號（code）`)
    }
    const code = raw.code.trim()

    if (raw.deleted === true) return // 墓碑不匯入

    const name = typeof raw.name === 'string' && raw.name !== '' ? raw.name : code
    const type: WatchlistItem['type'] = VALID_TYPES.includes(raw.type as WatchlistItem['type'])
      ? (raw.type as WatchlistItem['type'])
      : 'stock'
    const addedAt =
      typeof raw.addedAt === 'number' && Number.isFinite(raw.addedAt) ? raw.addedAt : Date.now()
    const updatedAt =
      typeof raw.updatedAt === 'number' && Number.isFinite(raw.updatedAt) ? raw.updatedAt : addedAt

    if (seen.has(code)) return // 依 code 去重（保留第一筆）
    seen.add(code)
    result.push({ code, name, type, addedAt, updatedAt })
  })

  return result
}