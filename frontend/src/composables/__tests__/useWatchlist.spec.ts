import { describe, it, expect, beforeEach } from 'vitest'
import { useWatchlist } from '../useWatchlist'

describe('useWatchlist', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  describe('add', () => {
    it('should add stock to watchlist', () => {
      const { add, items, isWatched } = useWatchlist()

      add('2330', '台積電', 'stock')

      expect(items.value.length).toBe(1)
      expect(items.value[0].code).toBe('2330')
      expect(items.value[0].name).toBe('台積電')
      expect(items.value[0].type).toBe('stock')
      expect(isWatched('2330')).toBe(true)
    })

    it('should not add duplicate stock', () => {
      const { add, items } = useWatchlist()

      add('2330', '台積電', 'stock')
      add('2330', '台積電', 'stock')

      expect(items.value.length).toBe(1)
    })

    it('should add multiple different stocks', () => {
      const { add, items } = useWatchlist()

      add('2330', '台積電', 'stock')
      add('0050', '元大台灣50', 'etf')

      expect(items.value.length).toBe(2)
    })
  })

  describe('remove', () => {
    it('should remove stock from watchlist', () => {
      const { add, remove, items, isWatched } = useWatchlist()

      add('2330', '台積電', 'stock')
      expect(items.value.length).toBe(1)

      remove('2330')
      expect(items.value.length).toBe(0)
      expect(isWatched('2330')).toBe(false)
    })

    it('should not affect other stocks when removing', () => {
      const { add, remove, items } = useWatchlist()

      add('2330', '台積電', 'stock')
      add('0050', '元大台灣50', 'etf')

      remove('2330')

      expect(items.value.length).toBe(1)
      expect(items.value[0].code).toBe('0050')
    })
  })

  describe('toggle', () => {
    it('should add stock when not watched', () => {
      const { toggle, items, isWatched } = useWatchlist()

      toggle('2330', '台積電', 'stock')

      expect(items.value.length).toBe(1)
      expect(isWatched('2330')).toBe(true)
    })

    it('should remove stock when watched', () => {
      const { add, toggle, items, isWatched } = useWatchlist()

      add('2330', '台積電', 'stock')
      expect(isWatched('2330')).toBe(true)

      toggle('2330', '台積電', 'stock')
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

      add('2330', '台積電', 'stock')

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

      add('2330', '台積電', 'stock')
      add('0050', '元大台灣50', 'etf')

      expect(watchedCodes.value.size).toBe(2)
      expect(watchedCodes.value.has('2330')).toBe(true)
      expect(watchedCodes.value.has('0050')).toBe(true)
    })
  })

  describe('sortedItems', () => {
    it('should sort by addedAt descending by default', async () => {
      const { add, sortedItems } = useWatchlist()

      add('0050', '元大台灣50', 'etf')
      // Ensure different timestamps
      await new Promise(resolve => setTimeout(resolve, 2))
      add('2330', '台積電', 'stock')

      expect(sortedItems.value[0].code).toBe('2330')
      expect(sortedItems.value[1].code).toBe('0050')
    })
  })

  describe('clear', () => {
    it('should remove all items', () => {
      const { add, clear, items } = useWatchlist()

      add('2330', '台積電', 'stock')
      add('0050', '元大台灣50', 'etf')
      expect(items.value.length).toBe(2)

      clear()
      expect(items.value.length).toBe(0)
    })
  })

  describe('localStorage', () => {
    it('should persist to localStorage', async () => {
      const { add } = useWatchlist()

      add('2330', '台積電', 'stock')

      // watchEffect runs asynchronously, wait for it
      await new Promise(resolve => setTimeout(resolve, 10))

      const stored = JSON.parse(localStorage.getItem('stockpayday-watchlist') || '[]')
      expect(stored.length).toBe(1)
      expect(stored[0].code).toBe('2330')
    })

    it('should load from localStorage on init', () => {
      localStorage.setItem('stockpayday-watchlist', JSON.stringify([
        { code: '2330', name: '台積電', type: 'stock', addedAt: Date.now() },
      ]))

      const { items, isWatched } = useWatchlist()

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
