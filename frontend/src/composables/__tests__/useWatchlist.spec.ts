import { describe, it, expect, beforeEach } from 'vitest'
import { useWatchlist } from '../useWatchlist'

describe('useWatchlist', () => {
  beforeEach(() => {
    localStorage.clear()
    useWatchlist().reset()
  })

  describe('add', () => {
    it('should add stock to watchlist', () => {
      const { add, items, isWatched } = useWatchlist()

      add('2330')

      expect(items.value.length).toBe(1)
      expect(items.value[0].code).toBe('2330')
      expect(isWatched('2330')).toBe(true)
    })

    it('should not add duplicate stock', () => {
      const { add, items } = useWatchlist()

      add('2330')
      add('2330')

      expect(items.value.length).toBe(1)
    })

    it('should add multiple different stocks', () => {
      const { add, items } = useWatchlist()

      add('2330')
      add('0050')

      expect(items.value.length).toBe(2)
    })
  })

  describe('remove', () => {
    it('should remove stock from watchlist', () => {
      const { add, remove, items, isWatched } = useWatchlist()

      add('2330')
      expect(items.value.length).toBe(1)

      remove('2330')
      expect(items.value.length).toBe(0)
      expect(isWatched('2330')).toBe(false)
    })

    it('should not affect other stocks when removing', () => {
      const { add, remove, items } = useWatchlist()

      add('2330')
      add('0050')

      remove('2330')

      expect(items.value.length).toBe(1)
      expect(items.value[0].code).toBe('0050')
    })
  })

  describe('toggle', () => {
    it('should add stock when not watched', () => {
      const { toggle, items, isWatched } = useWatchlist()

      toggle('2330')

      expect(items.value.length).toBe(1)
      expect(isWatched('2330')).toBe(true)
    })

    it('should remove stock when watched', () => {
      const { add, toggle, items, isWatched } = useWatchlist()

      add('2330')
      expect(isWatched('2330')).toBe(true)

      toggle('2330')
      expect(items.value.length).toBe(0)
      expect(isWatched('2330')).toBe(false)
    })
  })

  describe('isWatched', () => {
    it('should return false for unwatched stock', () => {
      const { isWatched } = useWatchlist()

      expect(isWatched('2330')).toBe(false)
    })

    it('should return true for watched stock', () => {
      const { add, isWatched } = useWatchlist()

      add('2330')

      expect(isWatched('2330')).toBe(true)
    })
  })

  describe('watchedCodes', () => {
    it('should return empty set when no items', () => {
      const { watchedCodes } = useWatchlist()

      expect(watchedCodes.value.size).toBe(0)
    })

    it('should return set of watched codes', () => {
      const { add, watchedCodes } = useWatchlist()

      add('2330')
      add('0050')

      expect(watchedCodes.value.size).toBe(2)
      expect(watchedCodes.value.has('2330')).toBe(true)
      expect(watchedCodes.value.has('0050')).toBe(true)
    })
  })

  describe('sortedItems', () => {
    it('should sort by addedAt descending by default', async () => {
      const { add, sortedItems } = useWatchlist()

      add('0050')
      // Ensure different timestamps
      await new Promise(resolve => setTimeout(resolve, 2))
      add('2330')

      expect(sortedItems.value[0].code).toBe('2330')
      expect(sortedItems.value[1].code).toBe('0050')
    })
  })

  describe('clear', () => {
    it('should remove all items', () => {
      const { add, clear, items } = useWatchlist()

      add('2330')
      add('0050')
      expect(items.value.length).toBe(2)

      clear()
      expect(items.value.length).toBe(0)
    })
  })

  describe('localStorage', () => {
    it('should persist to localStorage', async () => {
      const { add } = useWatchlist()

      add('2330')

      // watchEffect runs asynchronously, wait for it
      await new Promise(resolve => setTimeout(resolve, 10))

      const stored = JSON.parse(localStorage.getItem('stockpayday-watchlist') || '[]')
      expect(stored.length).toBe(1)
      expect(stored[0].code).toBe('2330')
    })

    it('should load from localStorage on init', () => {
      localStorage.setItem('stockpayday-watchlist', JSON.stringify([
        { code: '2330', addedAt: Date.now() },
      ]))

      const { items, isWatched } = useWatchlist()
      // Singleton: re-init from localStorage
      useWatchlist().reset()

      expect(items.value.length).toBe(1)
      expect(isWatched('2330')).toBe(true)
    })

    it('should handle invalid JSON in localStorage', () => {
      localStorage.setItem('stockpayday-watchlist', 'invalid-json')

      const { items } = useWatchlist()

      expect(items.value.length).toBe(0)
    })

    it('should handle non-array JSON in localStorage', () => {
      localStorage.setItem('stockpayday-watchlist', '{"not": "array"}')

      const { items } = useWatchlist()

      expect(items.value.length).toBe(0)
    })
  })
})



describe('useWatchlist — 功能 001（追蹤任意股票）', () => {
  beforeEach(() => {
    localStorage.clear()
    useWatchlist().reset()
  })

  it('連續 toggle 同一支股票（快速連點）最終狀態一致', () => {
    const { toggle, isWatched } = useWatchlist()

    toggle('2330')
    toggle('2330')
    toggle('2330')

    expect(isWatched('2330')).toBe(true)

    toggle('2330')
    expect(isWatched('2330')).toBe(false)
  })

  it('追蹤第 101 支股票無數量上限', () => {
    const { add, items } = useWatchlist()

    for (let i = 1; i <= 101; i++) {
      add(String(i).padStart(4, '0'))
    }

    expect(items.value.length).toBe(101)
  })

  it('localStorage.setItem 拋錯時追蹤操作仍成功（session 記憶、不 crash）', () => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = () => {
      throw new Error('quota exceeded')
    }
    try {
      const { toggle, isWatched, items } = useWatchlist()

      toggle('2330')

      expect(isWatched('2330')).toBe(true)
      expect(items.value).toHaveLength(1)
    } finally {
      Storage.prototype.setItem = original
    }
  })

  it('localStorage.getItem 拋錯時初始化回退空清單（不 crash）', () => {
    const original = Storage.prototype.getItem
    Storage.prototype.getItem = () => {
      throw new Error('access denied')
    }
    try {
      localStorage.clear()
      useWatchlist().reset()
      const { items } = useWatchlist()

      expect(items.value).toEqual([])
    } finally {
      Storage.prototype.getItem = original
    }
  })

  it('已下市股票保留於追蹤清單（不因無配息被過濾）', () => {
    const { add, isWatched, items } = useWatchlist()

    add('9999')

    expect(isWatched('9999')).toBe(true)
    expect(items.value.some(i => i.code === '9999')).toBe(true)
  })
})
