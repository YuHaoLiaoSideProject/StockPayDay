/**
 * useWatchlistExport 單元測試（Phase 9 子任務 C — 匯出/匯入備援工具）
 *
 * 對應測試計畫 2.5 匯出／匯入備援 util：
 * - F-21 匯出內容為目前追蹤項目，不含已移除的墓碑項目
 * - F-22 匯入合併且不重複（依 code 去重）
 * - F-23 匯入格式錯誤（非 JSON / 非陣列 / 缺 code）→ 拋出可辨識的 WatchlistImportError
 */
import { describe, it, expect } from 'vitest'
import type { WatchlistItem } from '../../types/watchlist'
import {
  exportWatchlistToText,
  parseWatchlistImportText,
  WatchlistImportError,
} from '../useWatchlistExport'

describe('exportWatchlistToText', () => {
  it('F-21 匯出僅含目前追蹤項目，不含已移除墓碑', () => {
    const items: WatchlistItem[] = [
      { code: '2330', addedAt: 1 },
      { code: '0056', addedAt: 2 },
      { code: '2884', addedAt: 3 },
      { code: '6666', addedAt: 4, deleted: true },
    ]

    const text = exportWatchlistToText(items)
    const parsed = JSON.parse(text) as WatchlistItem[]

    expect(parsed.map(i => i.code)).toEqual(['2330', '0056', '2884'])
    expect(parsed.some(i => i.deleted)).toBe(false)
    expect(text).not.toContain('6666')
  })

  it('空清單匯出為空陣列（可再次匯入）', () => {
    expect(exportWatchlistToText([])).toBe('[]')
  })
})

describe('parseWatchlistImportText', () => {
  it('F-22 匯入解析依 code 去重（重複 X 只留一筆，Y 保留）', () => {
    const text = JSON.stringify([
      { code: '2330', addedAt: 1 },
      { code: '2330', addedAt: 2 },
      { code: '0056', addedAt: 3 },
    ])

    const result = parseWatchlistImportText(text)
    expect(result.map(i => i.code)).toEqual(['2330', '0056'])
  })

  it('匯入內容中的墓碑（deleted: true）不恢復為追蹤項目', () => {
    const text = JSON.stringify([
      { code: '2330', addedAt: 1 },
      { code: '6666', addedAt: 2, deleted: true },
    ])

    const result = parseWatchlistImportText(text)
    expect(result.map(i => i.code)).toEqual(['2330'])
  })

  it('F-23 非 JSON 內容拋出可辨識的 WatchlistImportError', () => {
    expect(() => parseWatchlistImportText('not-a-json')).toThrowError(WatchlistImportError)
    expect(() => parseWatchlistImportText('not-a-json')).toThrowError('匯入格式錯誤')
  })

  it('F-23 非陣列（物件）內容拋出 WatchlistImportError', () => {
    expect(() => parseWatchlistImportText('{"code": "2330"}')).toThrowError(WatchlistImportError)
  })

  it('F-23 項目缺少有效 code（欄位錯誤）拋出 WatchlistImportError 並含筆數', () => {
    expect(() =>
      parseWatchlistImportText('[{"name":"無代號"}]')
    ).toThrowError('匯入格式錯誤：第 1 筆缺少有效的證券代號（code）')
    expect(() => parseWatchlistImportText('[{"code": 123}]')).toThrowError(WatchlistImportError)
  })

  it('F-23 項目非物件內容拋出 WatchlistImportError', () => {
    expect(() => parseWatchlistImportText('["2330"]')).toThrowError(WatchlistImportError)
  })

  it('匯入空陣列回傳空清單（不視為錯誤）', () => {
    expect(parseWatchlistImportText('[]')).toEqual([])
  })
})
