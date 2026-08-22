import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'
import WatchlistPage from '../../views/WatchlistView.vue'
import WatchlistView from '../WatchlistView.vue'
import { useWatchlist } from '../../composables/useWatchlist'
import { useUpcoming } from '../../composables/useUpcoming'
import type { UpcomingDividend } from '../../types/stock'

const mockSecuritiesIndex = [
  { code: '2330', name: '台積電' },
  { code: '2317', name: '鴻海' },
]

let mockUpcoming: UpcomingDividend[] = []

const mockFetch = vi.fn((url: unknown) => {
  const u = String(url)
  if (u.includes('securities-index')) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockSecuritiesIndex) })
  }
  if (u.includes('upcoming')) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockUpcoming) })
  }
  return Promise.resolve({ ok: false, json: () => Promise.resolve([]) })
})

let router: Router

beforeEach(async () => {
  localStorage.clear()
  useWatchlist().reset()
  mockUpcoming = []
  vi.stubGlobal('fetch', mockFetch)
  // 控制 upcoming 資料（module-level singleton 重載）
  await useUpcoming().load()
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>home</div>' } },
      { path: '/watchlist', component: WatchlistPage },
      { path: '/stock/:code', component: { template: '<div>stock</div>' } },
    ],
  })
})

describe('views/WatchlistView（追蹤清單頁）— 功能 001', () => {
  async function mountPage(): Promise<VueWrapper> {
    const wrapper = mount(WatchlistPage, { global: { plugins: [router] } })
    await flushPromises()
    return wrapper
  }

  it('頁面頂部顯示常駐搜尋欄（data-testid=watchlist-search）', async () => {
    const wrapper = await mountPage()

    const search = wrapper.find('[data-testid="watchlist-search"]')
    expect(search.exists()).toBe(true)
    expect(search.find('input.search-input').exists()).toBe(true)
  })

  it('結果列含 ❤️，點 ❤️ 加入追蹤且清單立即更新', async () => {
    const wrapper = await mountPage()
    const input = wrapper.find('[data-testid="watchlist-search"] .search-input')
    await input.trigger('focus')
    await input.setValue('2330')
    await flushPromises()

    const rows = wrapper.findAll('.search-result-item')
    expect(rows.length).toBeGreaterThan(0)
    expect(wrapper.findAll('.search-result-item .watchlist-btn').length).toBeGreaterThan(0)

    const { isWatched } = useWatchlist()
    expect(isWatched('2330')).toBe(false)

    await wrapper.find('.search-result-item .watchlist-btn').trigger('click')
    await flushPromises()

    expect(isWatched('2330')).toBe(true)
    // 追蹤清單立即更新（內層 WatchlistView 顯示該股票）
    expect(wrapper.text()).toContain('2330')
    expect(wrapper.text()).toContain('台積電')
    expect(wrapper.text()).toContain('已追蹤 1 支證券')
  })

  it('追蹤清單為空時搜尋欄仍可使用（空狀態搜尋加入、脫離空狀態）', async () => {
    const { items } = useWatchlist()
    expect(items.value).toHaveLength(0)

    const wrapper = await mountPage()
    // 空狀態引導顯示
    expect(wrapper.find('.watchlist-blank, .watchlist-empty').exists()).toBe(true)

    // 搜尋欄仍常駐可用
    const input = wrapper.find('[data-testid="watchlist-search"] .search-input')
    await input.trigger('focus')
    await input.setValue('2317')
    await flushPromises()
    expect(wrapper.findAll('.search-result-item').length).toBeGreaterThan(0)

    // 點 ❤️ 加入 → 清單立即出現該股票，不再為空
    await wrapper.find('.search-result-item .watchlist-btn').trigger('click')
    await flushPromises()
    expect(items.value).toHaveLength(1)
    expect(wrapper.text()).toContain('2317')
    expect(wrapper.find('.watchlist-blank, .watchlist-empty').exists()).toBe(false)
  })

  it('追蹤清單頁搜尋無結果顯示「找不到符合的證券」', async () => {
    const wrapper = await mountPage()
    const input = wrapper.find('[data-testid="watchlist-search"] .search-input')
    await input.trigger('focus')
    await input.setValue('XXXXX')
    await flushPromises()

    expect(wrapper.text()).toContain('找不到符合的證券')
  })
})

describe('components/WatchlistView（追蹤清單視圖）— 功能 001 無配息顯示', () => {
  async function mountView(): Promise<VueWrapper> {
    const wrapper = mount(WatchlistView, { global: { plugins: [router] } })
    await flushPromises()
    return wrapper
  }

  it('無配息股票顯示「無近期配息」', async () => {
    const { add } = useWatchlist()
    add('9999', '無配息股')

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('9999')
    expect(wrapper.text()).toContain('無近期配息')
  })

  it('已下市股票仍顯示於追蹤清單', async () => {
    const { add } = useWatchlist()
    add('6666', '已下市測試股')

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('已下市測試股')
    expect(wrapper.text()).toContain('無近期配息')
  })

  it('公布配息後自動顯示配息資訊（upcoming 重新載入）', async () => {
    const { add } = useWatchlist()
    add('2330', '台積電')

    const wrapper = await mountView()
    expect(wrapper.text()).toContain('無近期配息')

    // upcoming.json 更新後重新載入：computed 自動反應
    mockUpcoming = [
      { code: '2330', name: '台積電', type: '息', ex_date: '2026-09-01', cash_dividend: 3.5, stock_dividend: 0 },
    ]
    await useUpcoming().load()
    await flushPromises()

    expect(wrapper.text()).toContain('$3.50')
  })
})