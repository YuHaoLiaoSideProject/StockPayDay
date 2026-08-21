import { ref, computed, watchEffect } from 'vue'
import type { WatchlistItem, WatchlistSortBy } from '../types/watchlist'

const STORAGE_KEY = 'stockpayday-watchlist'

/**
 * 追蹤清單管理 composable
 *
 * 功能：
 * - 新增/移除追蹤股票
 * - 查詢是否已追蹤
 * - 取得追蹤清單（可排序）
 * - localStorage 持久化
 */
export function useWatchlist() {
  const items = ref<WatchlistItem[]>([])
  const sortBy = ref<WatchlistSortBy>('addedAt')

  // 初始化：從 localStorage 讀取（必須在 watchEffect 之前）
  function init(): void {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (Array.isArray(parsed)) {
          items.value = parsed
        }
      }
    } catch {
      // localStorage 讀取失敗，使用空列表
    }
  }

  // 先初始化，再設定自動儲存（避免 watchEffect 覆蓋已載入的資料）
  init()

  // 監聽變化，自動儲存
  watchEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items.value))
    } catch {
      // localStorage 寫入失敗（可能已滿）
    }
  })

  /**
   * 新增追蹤
   */
  function add(code: string, name: string, type: WatchlistItem['type'] = 'stock'): void {
    if (isWatched(code)) return

    items.value.push({
      code,
      name,
      type,
      addedAt: Date.now(),
    })
  }

  /**
   * 移除追蹤
   */
  function remove(code: string): void {
    items.value = items.value.filter(item => item.code !== code)
  }

  /**
   * 切換追蹤狀態（加入/移除）
   */
  function toggle(code: string, name: string, type: WatchlistItem['type'] = 'stock'): void {
    if (isWatched(code)) {
      remove(code)
    } else {
      add(code, name, type)
    }
  }

  /**
   * 查詢是否已追蹤
   */
  function isWatched(code: string): boolean {
    return items.value.some(item => item.code === code)
  }

  /**
   * 取得追蹤的證券代號集合
   */
  const watchedCodes = computed(() => {
    return new Set(items.value.map(item => item.code))
  })

  /**
   * 排序後的追蹤清單
   */
  const sortedItems = computed(() => {
    const sorted = [...items.value]

    switch (sortBy.value) {
      case 'addedAt':
        return sorted.sort((a, b) => b.addedAt - a.addedAt)
      case 'code':
        return sorted.sort((a, b) => a.code.localeCompare(b.code))
      case 'name':
        return sorted.sort((a, b) => a.name.localeCompare(b.name, 'zh-TW'))
      case 'nextDividend':
        return sorted
      default:
        return sorted
    }
  })

  /**
   * 清空追蹤清單
   */
  function clear(): void {
    items.value = []
  }

  return {
    items,
    sortBy,
    sortedItems,
    watchedCodes,
    add,
    remove,
    toggle,
    isWatched,
    clear,
  }
}
