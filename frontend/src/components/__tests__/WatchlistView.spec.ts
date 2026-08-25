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
  if (u.includes('dividends/')) {
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockUpcoming) })
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

  it('頁面顯示追蹤清單標題', async () => {
    const wrapper = await mountPage()
    expect(wrapper.text()).toContain('我的追蹤清單')
  })
})

describe('components/WatchlistView（追蹤清單視圖）— 功能 001 無配息顯示', () => {
  async function mountView(): Promise<VueWrapper> {
    const wrapper = mount(WatchlistView, { global: { plugins: [router] } })
    await flushPromises()
    return wrapper
  }

  it('無配息股票在列表模式顯示「無近期配息」', async () => {
    const { add } = useWatchlist()
    add('9999')

    const wrapper = await mountView()

    // 切換到列表模式
    await wrapper.find('[data-view="list"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('9999')
    expect(wrapper.text()).toContain('無近期配息')
  })

  it('已下市股票在列表模式仍顯示於追蹤清單', async () => {
    const { add } = useWatchlist()
    add('6666')

    const wrapper = await mountView()

    // 切換到列表模式
    await wrapper.find('[data-view="list"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('無近期配息')
  })

  it('公布配息後自動顯示配息資訊（upcoming 重新載入）', async () => {
    const { add } = useWatchlist()
    add('2330')

    const wrapper = await mountView()

    // 切換到列表模式
    await wrapper.find('[data-view="list"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('無近期配息')

    // upcoming.json 更新後重新載入：computed 自動反應
    mockUpcoming = [
      { code: '2330', name: '台積電', type: '息', ex_date: '2026-09-01', cash_dividend: 3.5, stock_dividend: 0 },
    ]
    await useUpcoming().load()
    await flushPromises()

    expect(wrapper.text()).toContain('$3.5')
  })
})
